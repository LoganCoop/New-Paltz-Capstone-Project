"""Small example demonstrating mock sensors."""
from .mocks import MockCamera, MockIMU, MockRangefinder


def main():
    cam = MockCamera(seed=0)
    imu = MockIMU(seed=0)
    rng = MockRangefinder(seed=0)

    for _ in range(3):
        print(cam.capture())
        print(imu.read())
        print(rng.distance())


if __name__ == "__main__":
    main()
