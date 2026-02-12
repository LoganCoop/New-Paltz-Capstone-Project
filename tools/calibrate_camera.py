import cv2
import numpy as np
import glob
import os

# Checkerboard dimensions (number of inner corners per row and column)
CHECKERBOARD = (7, 9)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

objpoints = [] # 3d points in real world space
imgpoints = [] # 2d points in image plane

import os
# Use images from absolute path to 'calib_images/' directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)).replace('/tools','')
CALIB_DIR = os.path.join(PROJECT_ROOT, 'calib_images')
images = glob.glob(os.path.join(CALIB_DIR, '*.jpg'))

if not images:
    print("No images found in calib_images/. Please capture checkerboard images and place them there.")
    exit(1)

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
        cv2.imshow('img', img)
        cv2.waitKey(100)
cv2.destroyAllWindows()

if len(objpoints) < 10:
    print("Not enough valid images for calibration. Try capturing more.")
    exit(1)

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

np.savez('camera_calib.npz', camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
print("Calibration complete. Saved as camera_calib.npz.")
