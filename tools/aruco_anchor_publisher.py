"""Detect ArUco markers and publish anchor poses to test_outputs.

Writes newline-delimited JSON records to `test_outputs/anchors_<timestamp>.jsonl`.
Each record contains: timestamp, markers: [{id, tvec, rvec}].

Usage: python3 tools/aruco_anchor_publisher.py --calib camera.npz --marker-length 0.05
"""
import argparse
import json
import time
from pathlib import Path

def load_calibration(path):
    import numpy as np

    data = np.load(path)
    return data["camera_matrix"], data["dist_coeffs"]


def main():
    parser = argparse.ArgumentParser(description="Publish ArUco anchor poses to a JSONL file")
    parser.add_argument("--calib", default=None, help=".npz with camera_matrix and dist_coeffs")
    parser.add_argument("--marker-length", type=float, default=0.05, help="Marker side length in meters")
    parser.add_argument("--out", default=None, help="Output jsonl path (default: test_outputs/anchors_<ts>.jsonl)")
    parser.add_argument("--rate", type=float, default=5.0, help="Frames per second to check")
    parser.add_argument("--display", action="store_true", help="Show detection preview")
    args = parser.parse_args()

    try:
        from picamera2 import Picamera2
    except Exception as e:
        raise SystemExit("picamera2 is required: sudo apt install -y python3-picamera2")

    try:
        import cv2
        import numpy as np
    except Exception:
        raise SystemExit("OpenCV is required: sudo apt install -y python3-opencv")

    cam_mtx = None
    dist = None
    if args.calib:
        cam_mtx, dist = load_calibration(args.calib)

    project_root = Path(__file__).resolve().parent.parent
    out_dir = project_root / "test_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.out:
        out_path = Path(args.out)
    else:
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"anchors_{ts}.jsonl"

    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (1280, 720)})
    camera.configure(config)
    camera.start()

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(dictionary)

    interval = 1.0 / max(args.rate, 0.1)
    with open(out_path, "a") as fh:
        try:
            while True:
                frame = camera.capture_array()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, _ = detector.detectMarkers(gray)
                rec = {"timestamp": time.time(), "markers": []}
                if ids is not None and len(ids) > 0:
                    ids_list = [int(x) for x in ids.flatten()]
                    if cam_mtx is not None and dist is not None:
                        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                            corners, args.marker_length, cam_mtx, dist
                        )
                        for idx, marker_id in enumerate(ids_list):
                            tvec = tvecs[idx][0].tolist()
                            rvec = rvecs[idx][0].tolist()
                            rec["markers"].append({"id": int(marker_id), "tvec": tvec, "rvec": rvec})
                    else:
                        # No pose, only ids and corner pixel coords
                        for idx, marker_id in enumerate(ids_list):
                            pts = corners[idx][0].astype(float).reshape(-1, 2).tolist()
                            rec["markers"].append({"id": int(marker_id), "corners": pts})

                fh.write(json.dumps(rec) + "\n")
                fh.flush()

                if args.display:
                    if ids is not None and len(ids) > 0:
                        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                    cv2.imshow("Aruco", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                time.sleep(interval)
        finally:
            camera.stop()
            if args.display:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
