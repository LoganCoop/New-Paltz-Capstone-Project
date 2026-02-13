import argparse
import json
import math
import socket
import time

import board
import busio
import serial
import adafruit_bno055


FRAME_HEADER = 0x59
FRAME_LENGTH = 9


def read_frame(port):
    while True:
        first = port.read(1)
        if not first:
            return None
        if first[0] != FRAME_HEADER:
            continue
        second = port.read(1)
        if not second:
            return None
        if second[0] != FRAME_HEADER:
            continue
        rest = port.read(FRAME_LENGTH - 2)
        if len(rest) != FRAME_LENGTH - 2:
            return None
        frame = bytes([FRAME_HEADER, FRAME_HEADER]) + rest
        checksum = sum(frame[0:8]) & 0xFF
        if checksum != frame[8]:
            continue
        return frame


def parse_frame(frame):
    distance_cm = frame[2] + (frame[3] << 8)
    strength = frame[4] + (frame[5] << 8)
    temp_raw = frame[6] + (frame[7] << 8)
    temperature_c = (temp_raw / 8.0) - 256.0
    return distance_cm, strength, temperature_c


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


def main():
    parser = argparse.ArgumentParser(
        description="Stream TF-Luna + BNO055 data over UDP as JSON."
    )
    parser.add_argument("--ip", required=True, help="Destination IP address")
    parser.add_argument("--udp-port", type=int, default=5005, help="Destination UDP port")
    parser.add_argument("--port", default="/dev/serial0", help="TF-Luna serial port")
    parser.add_argument("--baud", type=int, default=115200, help="TF-Luna baud rate")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial timeout seconds")
    parser.add_argument("--address", default="0x29", help="BNO055 I2C address (hex)")
    parser.add_argument("--imu-rate", type=float, default=30.0, help="IMU sample rate Hz")
    parser.add_argument("--no-pos", dest="include_pos", action="store_false", help="Do not compute/include world-space position in payload")
    parser.add_argument("--offset", nargs=3, type=float, default=[0.0, 0.0, 0.0], help="xyz offset (meters) from IMU frame to TF-Luna emitter")
    parser.add_argument("--point-file", default=None, help="Optional path to append JSONL points (one record per line)")
    args = parser.parse_args()

    address = int(args.address, 16)
    imu_interval = 1.0 / max(args.imu_rate, 0.1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (args.ip, args.udp_port)

    point_fp = None
    if args.point_file:
        point_fp = open(args.point_file, "a")

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)

    next_imu_time = 0.0
    last_quat = None

    with serial.Serial(args.port, args.baud, timeout=args.timeout) as port:
        while True:
            frame = read_frame(port)
            if frame is None:
                continue
            distance_cm, strength, temperature_c = parse_frame(frame)

            now = time.time()
            if now >= next_imu_time:
                last_quat = sensor.quaternion
                next_imu_time = now + imu_interval

            if last_quat is None:
                continue

            w, x, y, z = last_quat
            payload = {
                "t": now,
                "dist_cm": distance_cm,
                "strength": strength,
                "temp_c": temperature_c,
                "qw": w,
                "qx": x,
                "qy": y,
                "qz": z,
            }

            if args.include_pos:
                # compute world-space position for the measured point
                dist_m = float(distance_cm) / 100.0
                local_v = (0.0, 0.0, dist_m)
                # normalize quaternion
                norm = math.sqrt(w * w + x * x + y * y + z * z)
                if norm == 0:
                    q = (1.0, 0.0, 0.0, 0.0)
                else:
                    q = (w / norm, x / norm, y / norm, z / norm)
                world_v = rotate_vector_by_quat(q, local_v)
                ox, oy, oz = args.offset
                pos = (world_v[0] + ox, world_v[1] + oy, world_v[2] + oz)
                payload["pos_m"] = [pos[0], pos[1], pos[2]]

                if point_fp is not None:
                    point_record = {
                        "t": now,
                        "dist_m": dist_m,
                        "pos_m": payload["pos_m"],
                        "quat": {"qw": q[0], "qx": q[1], "qy": q[2], "qz": q[3]},
                    }
                    point_fp.write(json.dumps(point_record) + "\n")
                    point_fp.flush()
            data = json.dumps(payload).encode("utf-8")
            sock.sendto(data, dest)
    if point_fp is not None:
        point_fp.close()


if __name__ == "__main__":
    main()
