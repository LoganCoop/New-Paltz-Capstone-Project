import time
import os
import argparse

parser = argparse.ArgumentParser(description="Capture calibration images from a camera with preview and manual capture")
parser.add_argument("--num", type=int, default=20, help="Number of images to capture")
parser.add_argument("--interval", type=float, default=3.0, help="Seconds between automatic captures (ignored in manual mode)")
parser.add_argument("--out-dir", default="calib_images", help="Output directory")
parser.add_argument("--start-index", type=int, default=1, help="Starting image index")
parser.add_argument(
    "--backend",
    choices=["picamera2", "opencv"],
    default="picamera2",
    help="Camera backend to use",
)
parser.add_argument("--device", default="/dev/video0", help="Video device path or index for OpenCV")
parser.add_argument("--manual", action="store_true", help="Show preview and capture on keypress ('c' or space). If not set, images are captured automatically at --interval seconds.")
parser.add_argument("--width", type=int, default=1280, help="Capture width")
parser.add_argument("--height", type=int, default=720, help="Capture height")
args = parser.parse_args()

OUT_DIR = args.out_dir
os.makedirs(OUT_DIR, exist_ok=True)

# Try to import cv2
try:
    import cv2
except Exception:
    raise SystemExit("OpenCV is required: sudo apt install -y python3-opencv")

# Try picamera2 if requested
use_picamera2 = False
if args.backend == "picamera2":
    try:
        from picamera2 import Picamera2  # type: ignore
        use_picamera2 = True
    except Exception:
        print("picamera2 requested but not available; falling back to OpenCV VideoCapture")

cap = None
camera = None
if use_picamera2:
    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (args.width, args.height)})
    camera.configure(config)
    camera.start()
else:
    try:
        dev_index = int(args.device)
    except Exception:
        dev_index = args.device
    api_preference = 0
    if hasattr(cv2, "CAP_V4L2"):
        api_preference = cv2.CAP_V4L2
    try:
        cap = cv2.VideoCapture(dev_index, api_preference)
    except Exception:
        cap = cv2.VideoCapture(dev_index)
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    except Exception:
        pass

index = args.start_index
count = 0
last_time = 0.0

print("Preview: press 'c' or Space to capture, 'q' to quit")
cv2.namedWindow("Capture Preview", cv2.WINDOW_NORMAL)
while count < args.num:
    if use_picamera2 and camera is not None:
        frame = camera.capture_array()
    else:
        ret, frame = cap.read()
        if not ret:
            print("Warning: failed to read frame from VideoCapture")
            time.sleep(0.1)
            continue

    if frame is None or getattr(frame, 'size', 0) == 0:
        time.sleep(0.1)
        continue

    # Convert 4-channel to 3-channel if necessary
    if len(frame.shape) == 3 and frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    cv2.imshow("Capture Preview", frame)
    key = cv2.waitKey(1) & 0xFF

    do_capture = False
    if args.manual:
        if key == ord('c') or key == 32:
            do_capture = True
        elif key == ord('q'):
            print('User requested quit')
            break
    else:
        now = time.time()
        if now - last_time >= args.interval:
            do_capture = True
            last_time = now
        if key == ord('q'):
            print('User requested quit')
            break

    if do_capture:
        img_path = os.path.join(OUT_DIR, f"img{index:02d}.jpg")
        try:
            cv2.imwrite(img_path, frame)
            print(f"Saved {img_path}")
            index += 1
            count += 1
        except Exception as e:
            print(f"Failed to save {img_path}: {e}")

cv2.destroyAllWindows()
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
print(f"Done. Captured {count} images to {OUT_DIR}")
