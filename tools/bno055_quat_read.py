import argparse
import time

import board
import busio
import adafruit_bno055


def main():
    parser = argparse.ArgumentParser(description="Read BNO055 quaternion output over I2C.")
    parser.add_argument("--address", default="0x28", help="I2C address (hex), default 0x28")
    parser.add_argument("--rate", type=float, default=10.0, help="Output rate in Hz")
    args = parser.parse_args()

    address = int(args.address, 16)
    interval = 1.0 / max(args.rate, 0.1)

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)

    while True:
        quat = sensor.quaternion
        if quat is not None:
            w, x, y, z = quat
            timestamp = time.time()
            print(
                f"{timestamp:.3f} qw={w:.6f} qx={x:.6f} qy={y:.6f} qz={z:.6f}",
                flush=True,
            )
        time.sleep(interval)


if __name__ == "__main__":
    main()
