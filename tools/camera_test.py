import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Capture a test image with Pi Camera 3.")
    parser.add_argument("--output", default="camera_test.jpg", help="Output image path")
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    args = parser.parse_args()

    # Prefer picamera2 when available, but fall back to libcamera command-line tools.
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (args.width, args.height)})
        camera.configure(config)
        camera.start()
        camera.capture_file(args.output)
        camera.stop()
        print(f"Saved {args.output}")
        return
    except Exception:
        # Fall through to command-line fallback
        pass

    import shutil
    import subprocess

    # Try libcamera-jpeg, then libcamera-still
    for cmd in ("libcamera-jpeg", "libcamera-still"):
        path = shutil.which(cmd)
        if path:
            cli = [cmd, "-o", args.output, "-w", str(args.width), "-h", str(args.height)]
            try:
                subprocess.check_call(cli)
                print(f"Saved {args.output} using {cmd}")
                return
            except subprocess.CalledProcessError as e:
                print(f"{cmd} failed: {e}", file=sys.stderr)
                raise SystemExit(1)

    print(
        "No supported camera backend found. Install picamera2 (`sudo apt install -y python3-picamera2`) or ensure libcamera tools are installed (libcamera-jpeg).",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
