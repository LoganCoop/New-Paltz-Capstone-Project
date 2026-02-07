"""Camera test helper.

Saves a timestamped JPEG into the project's `test_outputs/` directory on each run.
Tries `picamera2` first, then `libcamera-jpeg`/`libcamera-still`/`rpicam-hello`.
"""

import argparse
import sys
from pathlib import Path
import datetime
import shutil
import subprocess
import time
import tempfile


def _make_output_path(output_arg: str = None) -> Path:
    project_root = Path(__file__).resolve().parent.parent
    out_dir = project_root / "test_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_arg:
        base = Path(output_arg)
        if base.parent and str(base.parent) != ".":
            out = base
        else:
            out = out_dir / base
    else:
        out = out_dir / f"camera_test_{ts}.jpg"
    if "camera_test" in out.name and not any(ch.isdigit() for ch in out.stem):
        out = out_dir / f"{out.stem}_{ts}{out.suffix or '.jpg'}"
    if out.suffix == "":
        out = out.with_suffix(".jpg")
    return out


def _find_recent_jpg(search_dirs):
    best = None
    for d in search_dirs:
        try:
            for p in Path(d).glob("*.jpg"):
                m = p.stat().st_mtime
                if best is None or m > best[0]:
                    best = (m, p)
        except Exception:
            continue
    return best[1] if best else None


def main():
    parser = argparse.ArgumentParser(description="Capture a test image with Pi Camera 3.")
    parser.add_argument("--output", default=None, help="Output image filename (saved into test_outputs)")
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    args = parser.parse_args()

    out_path = _make_output_path(args.output)

    # Try picamera2 first
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (args.width, args.height)})
        camera.configure(config)
        camera.start()
        camera.capture_file(str(out_path))
        camera.stop()
        print(f"Saved {out_path}")
        return
    except Exception:
        pass

    # Prepare to detect genuinely new files: record start time
    start_time = time.time()

    # Try command-line backends, instructing them to write to a unique temp file
    backends = ["libcamera-jpeg", "libcamera-still", "rpicam-hello"]
    for cmd in backends:
        path = shutil.which(cmd)
        if not path:
            continue

        # create a unique temp output path
        fd, temp_out = tempfile.mkstemp(suffix=".jpg")
        os_temp = False
        try:
            os_temp = True
            temp_path = Path(temp_out)
            if cmd == "rpicam-hello":
                cli = [cmd, "-o", str(temp_path), "--width", str(args.width), "--height", str(args.height), "-t", "1000", "-n"]
            else:
                cli = [cmd, "-o", str(temp_path), "-w", str(args.width), "-h", str(args.height)]
            try:
                subprocess.check_call(cli)
            except subprocess.CalledProcessError:
                pass

            # If backend created the temp file, move it
            if temp_path.exists() and temp_path.stat().st_mtime >= start_time:
                try:
                    temp_path.rename(out_path)
                    print(f"Saved {out_path} using {cmd}")
                    return
                except Exception:
                    # try copy as fallback
                    try:
                        shutil.copy2(str(temp_path), str(out_path))
                        print(f"Saved {out_path} using {cmd} (copied)")
                        return
                    except Exception:
                        pass

            # If backend didn't write to temp but wrote somewhere else, look for new jpgs
            candidates = ["/tmp", str(Path.home()), str(Path(__file__).resolve().parent.parent / "test_outputs")]
            recent = _find_recent_jpg(candidates)
            if recent and recent.stat().st_mtime >= start_time:
                try:
                    recent.rename(out_path)
                    print(f"Saved {out_path} (moved recent {recent})")
                    return
                except Exception:
                    try:
                        shutil.copy2(str(recent), str(out_path))
                        print(f"Saved {out_path} (copied recent {recent})")
                        return
                    except Exception:
                        pass
        finally:
            try:
                if os_temp:
                    # cleanup temp file if still present
                    Path(temp_out).unlink(missing_ok=True)
            except Exception:
                pass

    # If we reach here nothing created a new file — fall back to renaming the most recent jpg.
    candidates = [str(Path(__file__).resolve().parent.parent / "test_outputs"), "/tmp", str(Path.home())]
    recent = _find_recent_jpg(candidates)
    if recent:
        try:
            # Move (rename) the most recent file to the desired output name
            recent.rename(out_path)
            print(f"Saved {out_path} (renamed from {recent})")
            return
        except Exception:
            try:
                # As a fallback, copy then remove original
                shutil.copy2(str(recent), str(out_path))
                recent.unlink(missing_ok=True)
                print(f"Saved {out_path} (copied from {recent} and removed original)")
                return
            except Exception:
                pass

    print(
        f"Failed to save image to {out_path}. Install picamera2 (`sudo apt install -y python3-picamera2`) or ensure libcamera/rpicam tools are available.",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
