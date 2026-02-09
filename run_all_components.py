#!/usr/bin/env python3
"""Unified components tester.

Run hardware tests (delegates to tools/run_all_tests.py) or exercise
HAL mock components when hardware isn't available. Writes short
outputs to `test_outputs/` by default.

Examples:
  python3 run_all_components.py --mocks
  python3 run_all_components.py --hardware --duration 8
  python3 run_all_components.py --auto-detect
"""

from pathlib import Path
import argparse
import subprocess
import sys
import json


def run_mocks(out_dir: Path, samples: int = 3):
    from hal.mocks import MockCamera, MockIMU, MockRangefinder

    cam = MockCamera(seed=0)
    imu = MockIMU(seed=0)
    rng = MockRangefinder(seed=0)

    outputs = {"camera": [], "imu": [], "rangefinder": []}
    for _ in range(samples):
        outputs["camera"].append(cam.capture())
        outputs["imu"].append(imu.read())
        outputs["rangefinder"].append(rng.distance())

    out_path = out_dir / "mocks_output.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for kind in ("camera", "imu", "rangefinder"):
            for entry in outputs[kind]:
                fh.write(json.dumps({"kind": kind, **entry}) + "\n")

    print(f"Wrote mock outputs to {out_path}")


def run_hardware(args):
    # Delegate to the existing tools runner
    script = Path(__file__).resolve().parent / "tools" / "run_all_tests.py"
    if not script.exists():
        print(f"Hardware runner not found at {script}")
        return 2

    cmd = [sys.executable, str(script)]
    if args.auto_detect:
        cmd.append("--auto-detect")
    else:
        if args.all:
            cmd.append("--all")
        if args.duration is not None:
            cmd += ["--duration", str(args.duration)]
        if args.use_system_camera:
            cmd.append("--use-system-camera")

    # forward output directory
    cmd += ["--out-dir", str(args.out_dir)]

    print("Running hardware tests:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Run all connected component tests")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mocks", action="store_true", help="Run HAL mock sensors")
    group.add_argument("--hardware", action="store_true", help="Run hardware tests via tools/run_all_tests.py")

    parser.add_argument("--auto-detect", action="store_true", help="Ask tools runner to auto-detect devices (hardware mode)")
    parser.add_argument("--all", action="store_true", help="In hardware mode, run all tests")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration per hardware test (seconds)")
    parser.add_argument("--out-dir", default="test_outputs", help="Directory to write test outputs")
    parser.add_argument("--use-system-camera", action="store_true", help="Use system Python for camera tools when available")
    parser.add_argument("--samples", type=int, default=3, help="Number of samples to take for mock sensors")

    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    # Default behavior: prefer hardware when requested, otherwise run mocks
    if args.hardware or args.auto_detect:
        rc = run_hardware(args)
        sys.exit(rc)

    # If user didn't request hardware, run mocks
    run_mocks(out_dir, samples=args.samples)


if __name__ == "__main__":
    main()
