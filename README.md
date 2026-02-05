# New Paltz Capstone Project – LiDAR Scanner

## Project Ideas
**Date:** 1/21/2026

## Initial Idea
**LiDAR Scanner – Physical Computing**
- Raspberry Pi – Python or Arduino – C++
- Made for room scanning
- Environmental mapping
- Handheld and/or mobile
- 3D printed parts

## Overview
My current idea for the student-proposed project will be a LiDAR scanner that I will build and program myself. I want to use Arduino and/or Raspberry Pi parts for the hardware, as well as 3D printed parts to create housing for the Arduino components. I intend to write the software myself for the LiDAR mapping using the C++-based Arduino language, and/or using Python via a Raspberry Pi. As an add-on to this project, I'd like to make the scanner mobile if I have the time to do so, whether it is done via a drone or a handheld scanner. I believe that this project is a great blend of software and hardware and that it would be a great opportunity to develop my skills in combining both fields of technology. I personally have great experience with CAD and 3D printing, as well as all of the material I have covered during my time working on my computer science degree, so I believe this project would be a great way to improve and show my skills.

## Project Scope
1. **Coordinate Transformation:** Implementing the trigonometric algorithms necessary to map 1D distance readings into 3D space.
2. **Hardware-Software Integration:** Managing the “logic flow” between physical movement (motors) and data acquisition (sensors) to ensure sub-centimeter accuracy.
3. **Signal Processing:** Implementing filters to reduce sensor noise and handle “outlier” data points in complex environments.
4. **Mobility (Stretch Goal):** If time permits, the system will be adapted into a handheld form factor using an IMU (Inertial Measurement Unit) to allow for mobile scanning (SLAM – Simultaneous Localization and Mapping).
	- A Pi Camera 3 can be used for marker-based localization to reduce drift.

## Timeline Layout
- **Phase 1:** Component testing and basic 2D mapping.
- **Phase 2:** Integration of the Godot visualization and 3D data collection.
- **Phase 3:** Refinement of the visualization UI and final housing assembly.

## Initial TF-Luna UART Test
This project includes a small Python script to read TF-Luna frames over UART and print
distance data for quick sensor validation.

### Wiring Notes (TF-Luna to Raspberry Pi)
- Connect GND to GND.
- Connect TF-Luna TX to Pi RX (GPIO 15).
- Connect TF-Luna RX to Pi TX (GPIO 14).
- Provide 5V power to the TF-Luna (verify your model's voltage/logic levels in its datasheet).

### Setup
1. Enable the Pi UART (raspi-config) and reboot.
2. Install dependencies:
	- `python -m pip install -r requirements.txt`
3. Run the reader:
	- `python tools/tfluna_read.py --port /dev/serial0 --baud 115200`

### Output
Each line includes a timestamp, distance in cm, signal strength, and temperature in C.

## Initial BNO055 Quaternion Test
This project includes a small Python script to read BNO055 quaternion output over I2C.

### Wiring Notes (BNO055 to Raspberry Pi)
- Connect GND to GND.
- Connect VIN to 3.3V or 5V (check your board's regulator specs).
- Connect SDA to GPIO 2 (SDA).
- Connect SCL to GPIO 3 (SCL).

### Setup
1. Enable I2C on the Pi (raspi-config) and reboot.
2. Install dependencies:
	- `python -m pip install -r requirements.txt`
3. Run the reader:
	- `python tools/bno055_quat_read.py --address 0x28 --rate 10`

### Output
Each line includes a timestamp and quaternion components (qw, qx, qy, qz).

## Pi Prep Checklist
- Update packages and reboot after updates.
- Enable UART (disable serial console), I2C, and Camera in raspi-config.
- Install base tools: python3-venv, python3-pip, i2c-tools, libcamera-apps.
- Add your user to dialout for serial access and log out/in.

## Pi Camera 3 Tests and Marker Localization
Marker-based localization uses the Pi Camera 3 to detect known visual markers and provide
absolute reference points, which helps reduce drift compared to IMU-only integration.

### Camera Test
1. Install camera tools:
	- `sudo apt install -y python3-picamera2 libcamera-apps`
2. Run the test capture:
	- `python tools/camera_test.py --output camera_test.jpg`

### ArUco Marker Demo
1. Install dependencies:
	- `sudo apt install -y python3-opencv python3-picamera2`
2. Run marker detection:
	- `python tools/aruco_pose_demo.py --rate 10`


