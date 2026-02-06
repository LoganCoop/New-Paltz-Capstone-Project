#!/usr/bin/env python3
"""Unified test runner for attached sensors.

This script invokes the existing test scripts in the `tools/` folder and
captures short samples from each device so you can verify wiring and basic
operation on a Raspberry Pi.

Usage examples:
  python3 tools/run_all_tests.py --all --duration 10
  python3 tools/run_all_tests.py --bno --duration 20 --bno-address 0x28
"""

import argparse
import subprocess
import sys
from pathlib import Path
import os
import shutil
import time

try:
    import serial
except Exception:
    serial = None


HERE = Path(__file__).resolve().parent


def run_command(cmd, duration, out_path=None):
    print("Running:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        out, _ = proc.communicate(timeout=duration)
    except subprocess.TimeoutExpired:
        print("Timeout reached — terminating process")
        proc.terminate()
        out, _ = proc.communicate(timeout=5)

    text = out.decode(errors="replace") if out is not None else ""
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        print(f"Wrote output to {out_path}")
    else:
        print(text)


def run_bno(address, rate, duration, out_dir):
    script = str(HERE / "bno055_quat_read.py")
    cmd = [sys.executable, script, "--address", hex(address), "--rate", str(rate)]
    out_path = out_dir / "bno055_output.txt"
    run_command(cmd, duration, out_path)


def run_camera(output, width, height, duration, out_dir):
    script = str(HERE / "camera_test.py")
    out_image = out_dir / output
    # camera tool is often installed as a system package (picamera2). Allow
    # running it with the system Python when requested.
    cam_python = sys.executable
    if hasattr(run_camera, "use_system_python") and run_camera.use_system_python:
        cam_python = "/usr/bin/python3"
    cmd = [cam_python, script, "--output", str(out_image), "--width", str(width), "--height", str(height)]
    # camera_test exits after capture; duration not critical but honored
    run_command(cmd, duration, None)


def run_aruco(marker_length, calib, rate, duration, out_dir):
    script = str(HERE / "aruco_pose_demo.py")
    aruco_python = sys.executable
    if hasattr(run_aruco, "use_system_python") and run_aruco.use_system_python:
        aruco_python = "/usr/bin/python3"
    cmd = [aruco_python, script, "--marker-length", str(marker_length), "--rate", str(rate)]
    if calib:
        cmd += ["--calib", str(calib)]
    out_path = out_dir / "aruco_output.txt"
    run_command(cmd, duration, out_path)


def run_tfluna(port, baud, duration, out_dir):
    script = str(HERE / "tfluna_read.py")
    cmd = [sys.executable, script, "--port", port, "--baud", str(baud)]
    out_path = out_dir / "tfluna_output.txt"
    run_command(cmd, duration, out_path)


def main():
    parser = argparse.ArgumentParser(description="Run quick tests for attached sensors.")
    parser.add_argument("--all", action="store_true", help="Run all available tests sequentially")

    parser.add_argument("--duration", type=float, default=10.0, help="Run time per test (seconds)")

    # BNO055 options
    parser.add_argument("--bno", action="store_true", help="Run BNO055 quaternion reader")
    parser.add_argument("--bno-address", type=lambda x: int(x, 16), default=0x28)
    parser.add_argument("--bno-rate", type=float, default=10.0)

    # Camera / Aruco
    parser.add_argument("--camera", action="store_true", help="Capture a test camera image")
    parser.add_argument("--camera-output", default="camera_test.jpg")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--aruco", action="store_true", help="Run ArUco marker detector")
    parser.add_argument("--marker-length", type=float, default=0.05)
    parser.add_argument("--calib", default=None, help="Path to .npz calibration file")
    parser.add_argument("--aruco-rate", type=float, default=1.0)

    # TF-Luna
    parser.add_argument("--tfluna", action="store_true", help="Run TF-Luna UART reader")
    parser.add_argument("--tfluna-port", default="/dev/serial0")
    parser.add_argument("--tfluna-baud", type=int, default=115200)

    parser.add_argument("--out-dir", default="test_outputs")
    parser.add_argument("--use-system-camera", action="store_true", help="Run camera and aruco scripts with system Python (for picamera2 installed via apt)")
    parser.add_argument("--auto-detect", action="store_true", help="Auto-detect I2C and serial devices and run appropriate tests")

    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # If requested, set functions to use system python for camera/aruco
    if args.use_system_camera:
        run_camera.use_system_python = True
        run_aruco.use_system_python = True

    if args.auto_detect:
        # Try to detect I2C addresses (requires i2cdetect present)
        i2c_addresses = []
        i2cdetect = shutil.which("i2cdetect")
        if i2cdetect:
            try:
                out = subprocess.check_output([i2cdetect, "-y", "1"], stderr=subprocess.DEVNULL).decode()
                for line in out.splitlines():
                    parts = line.split()
                    for p in parts[1:]:
                        if p != "--":
                            try:
                                addr = int(p, 16)
                                i2c_addresses.append(addr)
                            except Exception:
                                pass
            except Exception:
                pass

        # If common BNO055 addresses present, run BNO test
        if 0x28 in i2c_addresses or 0x29 in i2c_addresses:
            addr = 0x28 if 0x28 in i2c_addresses else 0x29
            print(f"Detected BNO055 at 0x{addr:02x}, running BNO055 test")
            run_bno(addr, 10.0, args.duration, out_dir)
        else:
            print("No BNO055 detected on I2C addresses 0x28/0x29")

        # Detect serial ports and try to read a small sample to see activity
        candidate_ports = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0", "/dev/ttyUSB0"]
        found_port = None
        for p in candidate_ports:
            if os.path.exists(p):
                readable = False
                # try pyserial first
                if serial:
                    try:
                        with serial.Serial(p, 115200, timeout=0.5) as s:
                            data = s.read(64)
                            if data and len(data) > 0:
                                readable = True
                    except Exception:
                        readable = False
                else:
                    # fallback to invoking cat (may require permissions)
                    try:
                        proc = subprocess.Popen(["timeout", "2", "cat", p], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        out, _ = proc.communicate(timeout=3)
                        if out and len(out) > 0:
                            readable = True
                    except Exception:
                        readable = False

                if readable:
                    found_port = p
                    print(f"Detected serial activity on {p}")
                    break

        if found_port:
            run_tfluna(found_port, args.tfluna_baud, args.duration, out_dir)
        else:
            print("No serial activity detected on common ports")

        # After auto-detect mode, exit
        return

    # Determine what to run
    tasks = []
    if args.all or args.bno:
        tasks.append((run_bno, (args.bno_address, args.bno_rate, args.duration, out_dir)))
    if args.all or args.camera:
        tasks.append((run_camera, (args.camera_output, args.width, args.height, args.duration, out_dir)))
    if args.all or args.aruco:
        tasks.append((run_aruco, (args.marker_length, args.calib, args.aruco_rate, args.duration, out_dir)))
    if args.all or args.tfluna:
        tasks.append((run_tfluna, (args.tfluna_port, args.tfluna_baud, args.duration, out_dir)))

    if not tasks:
        print("Nothing selected to run. Use --all or specific --bno/--camera/--aruco/--tfluna flags.")
        raise SystemExit(1)

    for fn, params in tasks:
        try:
            fn(*params)
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
        except Exception as e:
            print(f"Error running test: {e}")

    # If requested, set functions to use system python for camera/aruco
    if args.use_system_camera:
        run_camera.use_system_python = True
        run_aruco.use_system_python = True


if __name__ == "__main__":
    main()
