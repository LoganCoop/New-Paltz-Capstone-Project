"""Hardware Abstraction Layer (HAL) package.

Provides abstract interfaces and mock implementations for sensors so
the rest of the pipeline can be developed without physical hardware.
"""
from .interfaces import Camera, IMU, Rangefinder
from .mocks import MockCamera, MockIMU, MockRangefinder

__all__ = [
    "Camera",
    "IMU",
    "Rangefinder",
    "MockCamera",
    "MockIMU",
    "MockRangefinder",
]
