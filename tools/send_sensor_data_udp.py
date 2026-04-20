import socket
import threading
import time
import json
import math
import argparse
import serial
import sys
import os
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
    # Robust initialization: retry until device responds
    interval = 1.0 / max(rate_hz, 0.1)
    sensor = None
    while sensor is None:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
        except Exception as e:
            print("BNO055 init error, retrying:", e, file=sys.stderr)
            time.sleep(1.0)

    # Read loop: catch and continue on transient read errors
    while True:
        try:
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
        except Exception as e:
            print("BNO055 read error (will retry):", e, file=sys.stderr)
            # attempt to recreate sensor on repeated errors
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
            except Exception:
                # if reinit fails, sleep and retry later
                time.sleep(1.0)
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
    parser.add_argument("--i2c-bus", type=int, default=1, help="I2C bus number (default 1)")
    parser.add_argument("--aruco-port", type=int, default=6006, help="UDP port to listen for ArUco detector packets (default 6006)")
    parser.add_argument("--simulate", action="store_true", help="Simulate sensors (no hardware required)")
    parser.add_argument("--fusion-alpha", type=float, default=0.2, help="EMA alpha for scanner_pose smoothing (0-1)")
    args = parser.parse_args()

    bno_address = int(args.bno_address, 16)
    send_interval = 1.0 / max(args.send_rate, 0.1)

    data = {}
    # Ensure Blinka uses the requested I2C bus
    os.environ.setdefault("I2C_BUS", str(args.i2c_bus))

    # Start ArUco UDP listener to receive marker detections from the camera process
    def aruco_listener(port, result_dict):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except Exception as e:
            print(f"Failed to bind ArUco listener on port {port}: {e}", file=sys.stderr)
            return
        sock.settimeout(0.5)
        while True:
            try:
                data_bytes, addr = sock.recvfrom(65536)
                try:
                    pkt = json.loads(data_bytes.decode('utf-8'))
                    result_dict['aruco'] = pkt
                except Exception:
                    continue
            except socket.timeout:
                continue
            except Exception as e:
                print("ArUco listener error:", e, file=sys.stderr)

    t_aruco = threading.Thread(target=aruco_listener, args=(args.aruco_port, data), daemon=True)
    t_aruco.start()
    # Start sensor threads (or simulated sensors)
    if not args.simulate:
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
    else:
        def simulate_sensors(result_dict, rate_hz):
            import random

            interval = 1.0 / max(rate_hz, 0.1)
            while True:
                # simulate TF-Luna frame
                result_dict['tfluna'] = {
                    'timestamp': time.time(),
                    'distance_cm': 100 + random.uniform(-5.0, 5.0),
                    'strength': 100,
                    'temp_c': 25.0,
                }
                # simulate BNO055 quaternion (identity-ish with small noise)
                result_dict['bno055'] = {
                    'timestamp': time.time(),
                    'qw': 1.0,
                    'qx': random.uniform(-0.01, 0.01),
                    'qy': random.uniform(-0.01, 0.01),
                    'qz': random.uniform(-0.01, 0.01),
                }
                time.sleep(interval)

        t_sim = threading.Thread(target=simulate_sensors, args=(data, args.bno_rate), daemon=True)
        t_sim.start()

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
                'aruco': data.get('aruco'),
                'dist_m': dist_m,
                'pos_m': pos_m,
            }
            # Build a simple scanner_pose combining ArUco position (if available)
            # and IMU orientation from BNO055. Position uses the first detected
            # marker tvec (meters) when present, otherwise falls back to the
            # TF-Luna-derived `pos_m`. Orientation uses the normalized
            # BNO055 quaternion.
            scanner_pose = None
            try:
                # orientation from BNO055
                b = data.get('bno055')
                if b is not None:
                    bw = float(b.get('qw', 1.0))
                    bx = float(b.get('qx', 0.0))
                    by = float(b.get('qy', 0.0))
                    bz = float(b.get('qz', 0.0))
                    n = math.sqrt(bw * bw + bx * bx + by * by + bz * bz)
                    if n == 0:
                        bw, bx, by, bz = 1.0, 0.0, 0.0, 0.0
                    else:
                        bw, bx, by, bz = bw / n, bx / n, by / n, bz / n
                    orientation = {'qw': bw, 'qx': bx, 'qy': by, 'qz': bz}
                else:
                    orientation = None

                # position from ArUco marker if available
                ar = data.get('aruco')
                position = None
                if ar and isinstance(ar, dict):
                    markers = ar.get('markers') or ar.get('marker_data') or []
                    if markers and len(markers) > 0:
                        m = markers[0]
                        tvec = m.get('tvec')
                        if tvec and len(tvec) >= 3:
                            # ArUco tvec is typically in meters in the camera frame.
                            position = [float(tvec[0]), float(tvec[1]), float(tvec[2])]

                            # If we have IMU orientation, rotate the camera-frame
                            # ArUco tvec into the world/IMU frame as a simple
                            # extrinsic approximation.
                            if orientation is not None:
                                q = (orientation['qw'], orientation['qx'], orientation['qy'], orientation['qz'])
                                try:
                                    rp = rotate_vector_by_quat(q, (position[0], position[1], position[2]))
                                    position = [rp[0], rp[1], rp[2]]
                                except Exception:
                                    pass

                # fallback to TF-Luna-derived pos_m
                if position is None and pos_m is not None:
                    position = pos_m

                # Apply simple exponential moving average smoothing to
                # reduce jitter in the reported scanner_pose.
                alpha = max(0.0, min(1.0, args.fusion_alpha))
                prev = data.get('scanner_pose_smoothed')
                smoothed = None
                if position is not None:
                    if prev and isinstance(prev, dict) and prev.get('position'):
                        pp = prev.get('position')
                        smoothed = [alpha * position[i] + (1.0 - alpha) * pp[i] for i in range(3)]
                    else:
                        smoothed = position
                    # store for next iteration
                    data['scanner_pose_smoothed'] = {'position': smoothed, 'timestamp': time.time()}

                scanner_pose = {
                    'timestamp': time.time(),
                    'position': smoothed if smoothed is not None else None,
                    'orientation': orientation,
                }
            except Exception:
                scanner_pose = None

            packet['scanner_pose'] = scanner_pose
            msg = json.dumps(packet).encode('utf-8')
            print("Sending packet:", json.dumps(packet))
            sock.sendto(msg, (args.ip, args.udp_port))
        time.sleep(send_interval)


if __name__ == "__main__":
    main()
