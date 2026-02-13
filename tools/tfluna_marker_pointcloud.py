#!/usr/bin/env python3
"""Capture marker points from TF-Luna + BNO055 and emit Unity-friendly output.

Defaults:
- Listen to TF-Luna on /dev/serial0 (115200)
- Read BNO055 over I2C at 0x29
- Trigger markers by sending any UDP packet to --listen-port (default 6006)
- Also allow pressing Enter in the terminal to record a marker
- Outputs appended JSON lines to `markers.jsonl` and also optionally forwarded to Unity via UDP

Usage examples:
  python tools/tfluna_marker_pointcloud.py --unity-ip 192.168.0.50 --unity-port 5005

"""
import argparse
import json
import math
import socket
import sys
import threading
import time

try:
    import board
    import busio
    import adafruit_bno055
except Exception:
    board = None
    busio = None
    adafruit_bno055 = None

import serial


FRAME_HEADER = 0x59
FRAME_LENGTH = 9


def read_tfluna_frame(port):
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
        distance_cm = frame[2] + (frame[3] << 8)
        strength = frame[4] + (frame[5] << 8)
        temp_raw = frame[6] + (frame[7] << 8)
        temperature_c = (temp_raw / 8.0) - 256.0
        return {
            "timestamp": time.time(),
            "distance_cm": distance_cm,
            "strength": strength,
            "temp_c": temperature_c,
        }


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
    # v' = q * (0, v) * q_conj
    qv = (0.0, v[0], v[1], v[2])
    qc = quat_conjugate(q)
    return quat_mul(quat_mul(q, qv), qc)[1:]


def tfluna_reader_thread(port_path, baud, timeout, shared):
    try:
        with serial.Serial(port_path, baud, timeout=timeout) as port:
            while True:
                frame = read_tfluna_frame(port)
                if frame is None:
                    continue
                shared['tfluna'] = frame
    except Exception as e:
        print("TF-Luna reader error:", e, file=sys.stderr)


def bno_reader_thread(address, rate_hz, shared):
    if busio is None or adafruit_bno055 is None:
        print("BNO055 libs not available; IMU disabled.")
        return
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
        interval = 1.0 / max(rate_hz, 0.1)
        while True:
            quat = sensor.quaternion
            if quat is not None:
                # sensor.quaternion returns (w,x,y,z)
                shared['bno055'] = {
                    'timestamp': time.time(),
                    'quat': tuple(quat),
                }
            time.sleep(interval)
    except Exception as e:
        print("BNO055 reader error:", e, file=sys.stderr)


def marker_listener_thread(listen_port, trigger_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", listen_port))
    sock.settimeout(0.5)
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data is not None:
                trigger_event.append({'t': time.time(), 'src': addr, 'payload': data})
        except socket.timeout:
            continue


def main():
    parser = argparse.ArgumentParser(description="TF-Luna marker point capture for Unity")
    parser.add_argument("--serial-port", default="/dev/serial0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--imu-address", default="0x29")
    parser.add_argument("--imu-rate", type=float, default=30.0)
    parser.add_argument("--unity-ip", help="Unity destination IP to send marker packets", default=None)
    parser.add_argument("--unity-port", type=int, default=5005)
    parser.add_argument("--listen-port", type=int, default=6006, help="UDP port to listen for marker triggers")
    parser.add_argument("--out-file", default="markers.jsonl", help="Append marker JSON lines here")
    parser.add_argument("--offset", nargs=3, type=float, default=[0.0, 0.0, 0.0], help="xyz offset (meters) from IMU frame to TF-Luna emitter")
    args = parser.parse_args()

    address = int(args.imu_address, 16)

    shared = {}

    # Start sensor threads
    t1 = threading.Thread(target=tfluna_reader_thread, args=(args.serial_port, args.baud, args.timeout, shared), daemon=True)
    t1.start()
    t2 = threading.Thread(target=bno_reader_thread, args=(address, args.imu_rate, shared), daemon=True)
    t2.start()

    # Marker trigger storage (simple list acting as queue)
    trigger_events = []
    t3 = threading.Thread(target=marker_listener_thread, args=(args.listen_port, trigger_events), daemon=True)
    t3.start()

    # UDP socket to Unity if requested
    if args.unity_ip:
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        unity_dest = (args.unity_ip, args.unity_port)
        print(f"Will send marker packets to {unity_dest}")
    else:
        send_sock = None

    seq = 0
    out_fp = open(args.out_file, "a")

    print("Ready. Press Enter to record a marker, or send any UDP packet to the listen port.")

    try:
        while True:
            # Check for keyboard Enter
            import select

            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                _ = sys.stdin.readline()
                trigger_events.append({'t': time.time(), 'src': ('local', 0), 'payload': b'enter'})

            if trigger_events:
                ev = trigger_events.pop(0)

                t_now = time.time()
                tfluna = shared.get('tfluna')
                bno = shared.get('bno055')

                if tfluna is None or bno is None:
                    print("Skipping marker: missing sensor data (wait for sensors to warm up)")
                    continue

                # compute point
                dist_m = float(tfluna['distance_cm']) / 100.0
                # use local forward vector along +Z in sensor frame
                local_v = (0.0, 0.0, dist_m)
                quat = bno['quat']
                # normalize quaternion
                qw, qx, qy, qz = quat
                norm = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
                if norm == 0:
                    print("Invalid quaternion; skipping")
                    continue
                q = (qw / norm, qx / norm, qy / norm, qz / norm)
                world_v = rotate_vector_by_quat(q, local_v)
                # apply offset (sensor position in IMU frame)
                ox, oy, oz = args.offset
                pos = (world_v[0] + ox, world_v[1] + oy, world_v[2] + oz)

                seq += 1
                record = {
                    'seq': seq,
                    't': t_now,
                    'marker_src': ev.get('src'),
                    'dist_m': dist_m,
                    'pos_m': [pos[0], pos[1], pos[2]],
                    'quat': {'qw': q[0], 'qx': q[1], 'qy': q[2], 'qz': q[3]},
                }

                # append to file
                out_fp.write(json.dumps(record) + '\n')
                out_fp.flush()

                # forward to Unity if configured
                if send_sock:
                    try:
                        send_sock.sendto(json.dumps({'type': 'marker', 'data': record}).encode('utf-8'), unity_dest)
                    except Exception as e:
                        print("Failed to send UDP to Unity:", e, file=sys.stderr)

                print(f"Recorded marker #{seq}: pos={record['pos_m']} dist={dist_m:.3f}m")

            # small sleep to reduce CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting")
    finally:
        out_fp.close()


if __name__ == '__main__':
    main()
