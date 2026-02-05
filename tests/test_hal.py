import sys


def run():
    from hal.mocks import MockCamera, MockIMU, MockRangefinder

    cam = MockCamera(seed=1)
    f1 = cam.capture()
    f2 = cam.capture()
    assert f2["frame_id"] == f1["frame_id"] + 1, "camera frame ids should increment"

    imu1 = MockIMU(seed=2)
    imu2 = MockIMU(seed=2)
    r1 = imu1.read()
    r2 = imu2.read()
    assert r1["accel"] == r2["accel"], "IMU seeded reads should match"

    rng = MockRangefinder(seed=3, base=1.5)
    d = rng.distance()["distance_m"]
    assert 1.4 <= d <= 1.6, "Rangefinder reading out of expected bounds"

    print("All HAL mock tests passed")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print("TEST FAILED:", e)
        sys.exit(1)
