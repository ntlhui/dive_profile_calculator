'''Dive Profile Descriptor
'''
import datetime as dt
from dataclasses import dataclass
from typing import List


@dataclass
class DiveProfilePoint:
    """Dive Profile point

    This point defines part of the dive profile.  The dive profile is interpolated between two
    profile points.
    """
    depth: float # in meters
    timestamp: dt.timedelta
    consumption: float # in liters per minute

@dataclass
class DiveProfile:
    """Dive Profile

    This defines the entirety of the dive profile and associated parameters.
    """
    gas_volume: float # in liters
    gas_pressure: float # in bar
    profile: List[DiveProfilePoint]
    water_density: float = 1023.6 # in kg/m^3
    gravity_constant: float = 9.80665 # m/s^2

    def ambient_pressure(self, depth: float) -> float:
        """Computes the ambient pressure at the specified depth

        Args:
            depth (float): Depth in meters

        Returns:
            float: Hydrostatic pressure in bar
        """
        return (self.water_density * self.gravity_constant * depth) * 1e-5 + 1
