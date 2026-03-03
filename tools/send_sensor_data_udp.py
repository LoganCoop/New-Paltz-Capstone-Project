import socket
import threading
import time
import json
import math
import argparse
import serial
import board
import busio
import adafruit_bno055

DEFAULT_TF_LUNA_PORT = "/dev/serial0"
DEFAULT_TF_LUNA_BAUD = 115200
DEFAULT_TF_LUNA_TIMEOUT = 1.0
DEFAULT_BNO055_ADDRESS = "0x29"
DEFAULT_BNO055_RATE_HZ = 10.0
DEFAULT_UDP_PORT = 5005
DEFAULT_SEND_RATE_HZ = 20.0
DEFAULT_TF_LUNA_OFFSET = (0.0, 0.0, 0.0)


def quat_conjugate(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def quat_mul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def rotate_vector_by_quat(q, v):
    qv = (0.0, v[0], v[1], v[2])
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, qv), qc)[1:]


def read_tfluna(port_path, baud, timeout, result_dict):
    FRAME_HEADER = 0x59
    FRAME_LENGTH = 9
    with serial.Serial(port_path, baud, timeout=timeout) as port:
        while True:
            first = port.read(1)
            if not first or first[0] != FRAME_HEADER:
                continue
            second = port.read(1)
            if not second or second[0] != FRAME_HEADER:
                continue
            rest = port.read(FRAME_LENGTH - 2)
            if len(rest) != FRAME_LENGTH - 2:
                continue
            frame = bytes([FRAME_HEADER, FRAME_HEADER]) + rest
            checksum = sum(frame[0:8]) & 0xFF
            if checksum != frame[8]:
                continue
            distance_cm = frame[2] + (frame[3] << 8)
            strength = frame[4] + (frame[5] << 8)
            temp_raw = frame[6] + (frame[7] << 8)
            temperature_c = (temp_raw / 8.0) - 256.0
            result_dict['tfluna'] = {
                'timestamp': time.time(),
                'distance_cm': distance_cm,
                'strength': strength,
                'temperature_c': temperature_c
            }


def read_bno055(result_dict, address, rate_hz):
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
    interval = 1.0 / max(rate_hz, 0.1)
    while True:
        quat = sensor.quaternion
        if quat is not None:
            w, x, y, z = quat
            result_dict['bno055'] = {
                'timestamp': time.time(),
                'qw': w,
                'qx': x,
                'qy': y,
                'qz': z
            }
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Stream TF-Luna + BNO055 data to the VR APK over UDP."
    )
    parser.add_argument("--ip", required=True, help="Quest headset IP address")
    parser.add_argument("--udp-port", type=int, default=DEFAULT_UDP_PORT, help="Destination UDP port")
    parser.add_argument("--tfluna-port", default=DEFAULT_TF_LUNA_PORT, help="TF-Luna serial port")
    parser.add_argument("--tfluna-baud", type=int, default=DEFAULT_TF_LUNA_BAUD, help="TF-Luna baud rate")
    parser.add_argument("--tfluna-timeout", type=float, default=DEFAULT_TF_LUNA_TIMEOUT, help="TF-Luna serial timeout")
    parser.add_argument("--bno-address", default=DEFAULT_BNO055_ADDRESS, help="BNO055 I2C address (hex), e.g. 0x28 or 0x29")
    parser.add_argument("--bno-rate", type=float, default=DEFAULT_BNO055_RATE_HZ, help="BNO055 sample rate in Hz")
    parser.add_argument("--send-rate", type=float, default=DEFAULT_SEND_RATE_HZ, help="UDP send rate in Hz")
    parser.add_argument("--offset", nargs=3, type=float, default=list(DEFAULT_TF_LUNA_OFFSET), help="XYZ sensor offset in meters")
    args = parser.parse_args()

    bno_address = int(args.bno_address, 16)
    send_interval = 1.0 / max(args.send_rate, 0.1)

    data = {}
    # Start sensor threads
    t1 = threading.Thread(
        target=read_tfluna,
        args=(args.tfluna_port, args.tfluna_baud, args.tfluna_timeout, data),
        daemon=True,
    )
    t2 = threading.Thread(
        target=read_bno055,
        args=(data, bno_address, args.bno_rate),
        daemon=True,
    )
    t1.start()
    t2.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Sending UDP packets to {args.ip}:{args.udp_port}")
    while True:
        if 'tfluna' in data and 'bno055' in data:
            # compute world-space point from TF-Luna distance and BNO055 quaternion
            try:
                distance_cm = data['tfluna'].get('distance_cm')
                dist_m = float(distance_cm) / 100.0
                qw = data['bno055'].get('qw')
                qx = data['bno055'].get('qx')
                qy = data['bno055'].get('qy')
                qz = data['bno055'].get('qz')
                norm = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
                if norm == 0:
                    q = (1.0, 0.0, 0.0, 0.0)
                else:
                    q = (qw / norm, qx / norm, qy / norm, qz / norm)

                local_v = (0.0, 0.0, dist_m)
                world_v = rotate_vector_by_quat(q, local_v)
                ox, oy, oz = args.offset
                pos_m = [world_v[0] + ox, world_v[1] + oy, world_v[2] + oz]
            except Exception:
                pos_m = None
                dist_m = None

            packet = {
                'tfluna': data['tfluna'],
                'bno055': data['bno055'],
                'dist_m': dist_m,
                'pos_m': pos_m,
            }
            msg = json.dumps(packet).encode('utf-8')
            sock.sendto(msg, (args.ip, args.udp_port))
        time.sleep(send_interval)


if __name__ == "__main__":
    main()
