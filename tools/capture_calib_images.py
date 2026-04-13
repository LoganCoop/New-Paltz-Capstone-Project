import time
import os
import argparse

parser = argparse.ArgumentParser(description="Capture calibration images from a camera")
parser.add_argument("--num", type=int, default=15, help="Number of images to capture")
parser.add_argument("--interval", type=float, default=3.0, help="Seconds between captures")
parser.add_argument("--out-dir", default="calib_images", help="Output directory")
parser.add_argument("--start-index", type=int, default=16, help="Starting image index")
parser.add_argument(
    "--backend",
    choices=["picamera2", "opencv"],
    default="opencv",
    help="Camera backend to use",
)
parser.add_argument("--device", default="/dev/video0", help="Video device path or index for OpenCV")
args = parser.parse_args()

OUT_DIR = args.out_dir
os.makedirs(OUT_DIR, exist_ok=True)

# Try picamera2 if requested
have_picamera2 = False
if args.backend == "picamera2":
    try:
        from picamera2 import Picamera2  # type: ignore
        have_picamera2 = True
    except Exception:
        have_picamera2 = False

if args.backend == "picamera2" and not have_picamera2:
    print("picamera2 requested but not available; falling back to OpenCV VideoCapture")

use_picamera2 = args.backend == "picamera2" and have_picamera2

if use_picamera2:
    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (1280, 720)})
    camera.configure(config)
    camera.start()
else:
    try:
        import cv2
    except Exception:
        raise SystemExit("OpenCV is required: sudo apt install -y python3-opencv")

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
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    except Exception:
        pass

index = args.start_index
for i in range(index, index + args.num):
    img_path = os.path.join(OUT_DIR, f"img{i}.jpg")
    print(f"Capturing {img_path} in {args.interval} seconds...")
    time.sleep(args.interval)
    try:
        if use_picamera2:
            frame = camera.capture_array()
            if frame is None or frame.size == 0:
                print(f"Failed to capture {img_path}: empty frame")
                continue
            # picamera2 returns numpy array BGR
            from PIL import Image
            im = Image.fromarray(frame)
            im.save(img_path)
        else:
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"Failed to capture {img_path}: VideoCapture read failed")
                continue
            try:
                import cv2

                cv2.imwrite(img_path, frame)
            except Exception as e:
                print(f"Failed to save {img_path}: {e}")
                continue
        print(f"Saved {img_path}")
    except Exception as e:
        print(f"Failed to capture {img_path}: {e}")

print("Done capturing calibration images.")
