import argparse
import time

import serial


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


def main():
    parser = argparse.ArgumentParser(description="Read TF-Luna frames over UART.")
    parser.add_argument("--port", default="/dev/serial0", help="Serial port path")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial timeout seconds")
    args = parser.parse_args()

    with serial.Serial(args.port, args.baud, timeout=args.timeout) as port:
        while True:
            frame = read_frame(port)
            if frame is None:
                continue
            distance_cm, strength, temperature_c = parse_frame(frame)
            timestamp = time.time()
            print(
                f"{timestamp:.3f} dist_cm={distance_cm} strength={strength} temp_c={temperature_c:.2f}",
                flush=True,
            )


if __name__ == "__main__":
    main()
