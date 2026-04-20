import argparse
import cv2
import numpy as np
import glob
import os


def main():
    parser = argparse.ArgumentParser(description="Calibrate camera from checkerboard images in calib_images/")
    parser.add_argument("--rows", type=int, default=5, help="Number of inner corners per row (width)")
    parser.add_argument("--cols", type=int, default=4, help="Number of inner corners per column (height)")
    parser.add_argument("--dir", default="calib_images", help="Directory with calibration images")
    parser.add_argument("--out", default="camera_calib.npz", help="Output .npz path")
    args = parser.parse_args()

    CHECKERBOARD = (args.rows, args.cols)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

    objpoints = []
    imgpoints = []

    images = sorted(glob.glob(os.path.join(args.dir, "*.jpg")))
    if not images:
        print(f"No images found in {args.dir}. Please capture checkerboard images and place them there.")
        return 1

    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            print(f"Failed to read {fname}")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
            cv2.imshow('img', img)
            cv2.waitKey(100)

    cv2.destroyAllWindows()

    if len(objpoints) < 6:
        print(f"Not enough valid images for calibration (found {len(objpoints)}). Try capturing more.")
        return 2

    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    np.savez(args.out, camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
    print(f"Calibration complete. Saved as {args.out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
