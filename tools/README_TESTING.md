Pi Sensor Test Instructions
===========================

Quick instructions to install prerequisites and run the per-device tests on a Raspberry Pi.

Prerequisites (Raspberry Pi OS):

- Enable I2C and Serial and Camera (use `raspi-config` UI).
- Update system and install OS packages for camera/OpenCV:

```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv python3-picamera2
```

- Install Python dependencies from the repository:

```bash
pip3 install --user -r requirements.txt
```

Hardware notes:
- BNO055: connected via I2C (SDA, SCL). Default address 0x28.
- TF-Luna: connected via UART (e.g., /dev/serial0). Default 115200 baud.
- Camera: Pi Camera 3 or compatible (Picamera2).

Running tests
-------------

Run all tests sequentially (each for 10 seconds by default):

```bash
python3 tools/run_all_tests.py --all --duration 10
```

Run a single test (examples):

```bash
# Capture a camera image
python3 tools/run_all_tests.py --camera --duration 5 --camera-output test.jpg

# Read BNO055 for 20 seconds
python3 tools/run_all_tests.py --bno --duration 20 --bno-address 0x28

# Read TF-Luna on serial port
python3 tools/run_all_tests.py --tfluna --duration 15 --tfluna-port /dev/serial0

# Run only ArUco detection (provide --calib if you have calibration .npz)
python3 tools/run_all_tests.py --aruco --duration 15 --marker-length 0.05 --calib camera_calib.npz
```

Outputs
-------

All textual outputs are written to `test_outputs/` by default. Camera images are saved there as well.

If something fails, please paste the `test_outputs/*.txt` logs and I can help interpret them.
