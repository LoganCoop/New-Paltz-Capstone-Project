"""Detect ArUco markers and publish anchor poses to test_outputs.

Writes newline-delimited JSON records to `test_outputs/anchors_<timestamp>.jsonl`.
Each record contains: timestamp, markers: [{id, tvec, rvec}].

Usage: python3 tools/aruco_anchor_publisher.py --calib camera.npz --marker-length 0.05
"""
import argparse
import json
import time
import socket
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
    parser.add_argument(
        "--backend",
        choices=["picamera2", "opencv"],
        default="picamera2",
        help="Camera backend to use: 'picamera2' or 'opencv' (VideoCapture device)",
    )
    parser.add_argument(
        "--device",
        default="/dev/video0",
        help="Video device path or numeric index for OpenCV backend (e.g. /dev/video0 or 0)",
    )
    parser.add_argument("--display", action="store_true", help="Show detection preview")
    parser.add_argument("--ip", default=None, help="Destination UDP IP to send anchor packets (optional)")
    parser.add_argument("--udp-port", type=int, default=5005, help="Destination UDP port")
    args = parser.parse_args()

    # Try to import picamera2 if available; OpenCV fallback will be used if requested.
    have_picamera2 = False
    try:
        from picamera2 import Picamera2  # type: ignore
        have_picamera2 = True
    except Exception:
        have_picamera2 = False

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

    cap = None
    camera = None
    use_picamera2 = args.backend == "picamera2" and have_picamera2
    use_opencv = args.backend == "opencv" or (args.backend == "picamera2" and not have_picamera2)

    if use_picamera2:
        camera = Picamera2()
        config = camera.create_preview_configuration(main={"size": (1280, 720)})
        camera.configure(config)
        camera.start()
    elif use_opencv:
        device = args.device
        try:
            dev_index = int(device)
        except Exception:
            dev_index = device

        api_preference = 0
        if hasattr(cv2, "CAP_V4L2"):
            api_preference = cv2.CAP_V4L2

        try:
            cap = cv2.VideoCapture(dev_index, api_preference)
        except Exception:
            cap = cv2.VideoCapture(dev_index)

        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        except Exception:
            pass

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(dictionary)

    interval = 1.0 / max(args.rate, 0.1)

    sock = None
    if args.ip:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with open(out_path, "a") as fh:
        try:
            while True:
                if use_picamera2:
                    frame = camera.capture_array()
                else:
                    ret, frame = cap.read()
                    if not ret:
                        print("Warning: failed to read frame from VideoCapture")
                        time.sleep(interval)
                        continue

                if frame is None or frame.size == 0:
                    print("Warning: Empty frame captured from camera.")
                    time.sleep(interval)
                    continue

                # Convert 4-channel to 3-channel if necessary
                if len(frame.shape) == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

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

                # Send over UDP if requested
                if sock is not None:
                    try:
                        msg = json.dumps(rec).encode("utf-8")
                        sock.sendto(msg, (args.ip, args.udp_port))
                    except Exception as e:
                        print("Warning: failed to send UDP packet:", e)

                if args.display:
                    if ids is not None and len(ids) > 0:
                        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                    cv2.imshow("Aruco", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                time.sleep(interval)
        finally:
            if use_picamera2 and camera is not None:
                try:
                    camera.stop()
                except Exception:
                    pass
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            if args.display:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
