"""Mock sensor implementations for development without hardware."""
import time
import random

from .interfaces import Camera, IMU, Rangefinder


class MockCamera(Camera):
    def __init__(self, seed=None):
        self._rand = random.Random(seed)
        self._counter = 0

    def capture(self):
        """Return a tiny metadata-only frame placeholder."""
        self._counter += 1
        return {
            "timestamp": time.time(),
            "frame_id": self._counter,
            "data": f"mock-frame-{self._counter}",
        }


class MockIMU(IMU):
    def __init__(self, seed=None):
        self._rand = random.Random(seed)

    def read(self):
        return {
            "timestamp": time.time(),
            "accel": [self._rand.uniform(-1.0, 1.0) for _ in range(3)],
            "gyro": [self._rand.uniform(-180.0, 180.0) for _ in range(3)],
            "quat": [self._rand.uniform(-1.0, 1.0) for _ in range(4)],
        }


class MockRangefinder(Rangefinder):
    def __init__(self, seed=None, base=1.0):
        self._rand = random.Random(seed)
        self.base = base

    def distance(self):
        return {
            "timestamp": time.time(),
            "distance_m": self.base + self._rand.uniform(-0.1, 0.1),
        }
