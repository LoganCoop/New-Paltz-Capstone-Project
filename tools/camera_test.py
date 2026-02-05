import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Capture a test image with Pi Camera 3.")
    parser.add_argument("--output", default="camera_test.jpg", help="Output image path")
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    args = parser.parse_args()

    try:
        from picamera2 import Picamera2
    except ImportError:
        print(
            "picamera2 is not installed. On Raspberry Pi OS, run: sudo apt install -y python3-picamera2",
            file=sys.stderr,
        )
        raise SystemExit(1)

    camera = Picamera2()
    config = camera.create_still_configuration(main={"size": (args.width, args.height)})
    camera.configure(config)
    camera.start()
    camera.capture_file(args.output)
    camera.stop()
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
