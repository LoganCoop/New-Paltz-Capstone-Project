import subprocess
import time
import os

# Number of calibration images to take
NUM_IMAGES = 15
# Interval between images (seconds)
INTERVAL = 3
# Output directory
OUT_DIR = "calib_images"

os.makedirs(OUT_DIR, exist_ok=True)

# Start from img16.jpg
START_INDEX = 16

for i in range(START_INDEX, START_INDEX + NUM_IMAGES):
    img_path = os.path.join(OUT_DIR, f"img{i}.jpg")
    print(f"Capturing {img_path} in 3 seconds...")
    time.sleep(INTERVAL)
    cmd = ["rpicam-still", "-o", img_path]
    try:
        subprocess.run(cmd, check=True)
        print(f"Saved {img_path}")
    except Exception as e:
        print(f"Failed to capture {img_path}: {e}")
print("Done capturing calibration images.")
