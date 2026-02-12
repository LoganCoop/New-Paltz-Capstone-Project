import argparse
import sys
import time

import numpy as np


def load_calibration(path):
    data = np.load(path)
    camera_matrix = data.get("camera_matrix")
    dist_coeffs = data.get("dist_coeffs")
    if camera_matrix is None or dist_coeffs is None:
        raise ValueError("Calibration file must contain camera_matrix and dist_coeffs.")
    return camera_matrix, dist_coeffs


def main():
        import socket
        import json
        UDP_IP = "192.168.0.198"
        UDP_PORT = 5005
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    import socket
    import json

    # UDP config for Unity
    UDP_IP = "192.168.0.198"
    UDP_PORT = 5005
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    parser = argparse.ArgumentParser(description="Detect ArUco markers with Pi Camera 3.")
    parser.add_argument("--marker-length", type=float, default=0.05, help="Marker side length (meters)")
    parser.add_argument("--calib", default=None, help="Path to .npz with camera_matrix and dist_coeffs")
    parser.add_argument("--rate", type=float, default=10.0, help="Detection rate in Hz")
    parser.add_argument("--display", action="store_true", help="Show a live preview window")
    args = parser.parse_args()

    try:
        from picamera2 import Picamera2
    except ImportError:
        print(
            "picamera2 is not installed. On Raspberry Pi OS, run: sudo apt install -y python3-picamera2",
            file=sys.stderr,
        )
        raise SystemExit(1)

    try:
        import cv2
    except ImportError:
        print(
            "OpenCV is not installed. On Raspberry Pi OS, run: sudo apt install -y python3-opencv",
            file=sys.stderr,
        )
        raise SystemExit(1)

    camera_matrix = None
    dist_coeffs = None
    if args.calib:
        camera_matrix, dist_coeffs = load_calibration(args.calib)

    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (1280, 720)})
    camera.configure(config)
    camera.start()

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(dictionary)

    interval = 1.0 / max(args.rate, 0.1)
    try:
        while True:
            frame = camera.capture_array()
            if frame is None or frame.size == 0:
                print("Warning: Empty frame captured from camera.", file=sys.stderr)
                time.sleep(interval)
                continue
            # Convert 4-channel (BGRA/RGBA) to 3-channel BGR if needed
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            else:
                frame_bgr = frame
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = detector.detectMarkers(gray)

            marker_data = []
            if ids is not None and len(ids) > 0:
                ids_list = [int(x) for x in ids.flatten()]
                print(f"markers={ids_list}")

                if camera_matrix is not None and dist_coeffs is not None:
                    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                        corners, args.marker_length, camera_matrix, dist_coeffs
                    )
                    for idx, marker_id in enumerate(ids_list):
                        tvec = tvecs[idx][0]
                        print(
                            f"id={marker_id} tvec_m=({tvec[0]:.3f}, {tvec[1]:.3f}, {tvec[2]:.3f})"
                        )
                        marker_data.append({
                            "id": marker_id,
                            "tvec": [float(tvec[0]), float(tvec[1]), float(tvec[2])]
                        })

            # Send marker data over UDP if any markers detected
            if marker_data:
                packet = {"timestamp": time.time(), "markers": marker_data}
                try:
                    msg = json.dumps(packet).encode('utf-8')
                    sock.sendto(msg, (UDP_IP, UDP_PORT))
                    print(f"Sent UDP packet to {UDP_IP}:{UDP_PORT}")
                except Exception as e:
                    print(f"Warning: Failed to send UDP packet: {e}", file=sys.stderr)

            if args.display and frame is not None and frame.size != 0:
                # Use frame_bgr for display (guaranteed 3-channel BGR)
                frame_disp = frame_bgr
                try:
                    cv2.aruco.drawDetectedMarkers(frame_disp, corners, ids)
                except Exception as e:
                    print(f"Warning: drawDetectedMarkers failed: {e}", file=sys.stderr)
                cv2.imshow("Aruco", frame_disp)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            time.sleep(interval)
    finally:
        camera.stop()
        if args.display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
