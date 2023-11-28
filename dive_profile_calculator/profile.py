'''Dive Profile Descriptor
'''
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Union

from schema import Schema, Optional, Or


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

    profile_schema = Schema({
        'gas_volume': Or(float, int),
        'gas_pressure': Or(float, int),
        Optional('water_density', default=1023.6): Or(float, int),
        Optional('gravity_constant', default=9.80665): Or(float, int),
        'profile': {
            int: {
                'depth': Or(float, int),
                'consumption': Or(float, int)
            }
        }
    })
    @classmethod
    def from_dict(cls, data: Any) -> DiveProfile:
        """Loads profile from dictionary

        Args:
            data (Any): Dict-like profile data

        Returns:
            DiveProfile: Initialized dive profile
        """
        valid_data: Dict[str, Any] = cls.profile_schema.validate(data)
        profile_data: Dict[int, Dict[str, Union[float, int]]] = valid_data['profile']
        gas_volume = float(valid_data['gas_volume'])
        gas_pressure = float(valid_data['gas_pressure'])
        water_density = float(valid_data['water_density'])
        gravity_constant = float(valid_data['gravity_constant'])
        profile_points: List[DiveProfilePoint] = []
        profile_points = [DiveProfilePoint(
            depth=float(point_parameters['depth']),
            timestamp=dt.timedelta(seconds=profile_timestamp),
            consumption=float(point_parameters['consumption'])
        ) for profile_timestamp, point_parameters in profile_data.items()]
        profile_points = sorted(profile_points, key=lambda x: x.timestamp)
        return DiveProfile(
            gas_volume=gas_volume,
            gas_pressure=gas_pressure,
            profile=profile_points,
            water_density=water_density,
            gravity_constant=gravity_constant
        )
