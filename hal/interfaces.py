from abc import ABC, abstractmethod


class Camera(ABC):
    """Abstract camera interface."""

    @abstractmethod
    def capture(self):
        """Capture a single frame.

        Returns a dict with at least a `timestamp` and `frame_id` or `data`.
        """


class IMU(ABC):
    """Abstract IMU interface."""

    @abstractmethod
    def read(self):
        """Return a single IMU reading (accel, gyro, quat) as a dict."""


class Rangefinder(ABC):
    """Abstract rangefinder/sonar interface."""

    @abstractmethod
    def distance(self):
        """Return the latest distance reading (meters) as a dict."""
