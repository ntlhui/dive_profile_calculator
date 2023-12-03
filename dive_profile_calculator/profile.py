'''Dive Profile Descriptor
'''
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Union

import numpy as np
from schema import Optional, Or, Schema


@dataclass
class DiveProfilePoint:
    """Dive Profile point

    This point defines part of the dive profile.  The dive profile is interpolated between two
    profile points.
    """
    depth: float  # in meters
    timestamp: dt.timedelta
    consumption: float  # in liters per minute


@dataclass
class DiveProfileSegment:
    """Dive profile segment
    """
    avg_depth: float  # in meters
    duration: dt.timedelta
    avg_consumption: float  # in liters per minute

    @classmethod
    def from_profile_points(cls,
                            first: DiveProfilePoint,
                            second: DiveProfilePoint) -> DiveProfileSegment:
        """Computes the dive segments

        Args:
            first (DiveProfilePoint): Starting point
            second (DiveProfilePoint): Ending point

        Returns:
            DiveProfileSegment: Dive segment
        """
        return DiveProfileSegment(
            avg_depth=np.average([first.depth, second.depth]),
            duration=second.timestamp - first.timestamp,
            avg_consumption=np.average([first.consumption, second.consumption])
        )


@dataclass
class DiverConfiguration:
    """Diver Configuration
    """
    gas_volume: float  # in l
    gas_pressure: float  # in bar
    consumption: float = 15  # in l/min
    water_density: float = 1023.6  # in kg/m^3
    gravity_constant: float = 9.80665  # m/s^2


@dataclass
class DiveProfile:
    """Dive Profile

    This defines the entirety of the dive profile and associated parameters.
    """
    gas_volume: float  # in liters
    gas_pressure: float  # in bar
    profile: List[DiveProfilePoint]
    water_density: float = 1023.6  # in kg/m^3
    gravity_constant: float = 9.80665  # m/s^2

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
        profile_data: Dict[int, Dict[str, Union[float, int]]
                           ] = valid_data['profile']
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

    def get_segments(self) -> List[DiveProfileSegment]:
        """Returns the profile segments

        Returns:
            List[DiveProfileSegment]: Dive profile segments
        """
        return [DiveProfileSegment.from_profile_points(self.profile[idx], self.profile[idx + 1])
                for idx in range(len(self.profile) - 1)]

    @staticmethod
    def compute_ssi_ascent(depth: float,
                           configuration: DiverConfiguration) -> List[DiveProfilePoint]:
        """Computes the SSI Recreational Ascent profile

        Args:
            depth (float): Depth in meters
            configuration (DiverConfiguration): Gas configuration

        Raises:
            RuntimeError: Trivial Ascent

        Returns:
            List[DiveProfilePoint]: List of dive profile points
        """
        if depth <= 0:
            raise RuntimeError('Trivial ascent')
        ascent_rate = 10  # m/min
        stop_duration = 3  # min
        stop_depth = 6  # min
        current_time = dt.timedelta(seconds=0)
        profile = [DiveProfilePoint(depth=depth,
                                    timestamp=current_time,
                                    consumption=configuration.consumption)]

        # 10 m/min to 6 m
        current_time += dt.timedelta(minutes=(depth -
                                     stop_depth) / ascent_rate)
        depth = stop_depth
        profile.append(DiveProfilePoint(depth=depth,
                                        timestamp=current_time,
                                        consumption=configuration.consumption))

        # stop
        current_time += dt.timedelta(minutes=stop_duration)
        profile.append(DiveProfilePoint(depth=depth,
                                        timestamp=current_time,
                                        consumption=configuration.consumption))

        # ascent to surface
        current_time += dt.timedelta(minutes=stop_depth / ascent_rate)
        depth = 0
        profile.append(DiveProfilePoint(depth=depth,
                                        timestamp=current_time,
                                        consumption=configuration.consumption))

        return profile

    @staticmethod
    def compute_gue_ascent(depth: float,
                           configuration: DiverConfiguration) -> List[DiveProfilePoint]:
        """Computes the GUE Minimum Deco profile

        Args:
            depth (float): Depth in meters
            configuration (DiverConfiguration): Gas configuration

        Raises:
            RuntimeError: Trivial Ascent

        Returns:
            List[DiveProfilePoint]: List of dive profile points
        """
        if depth <= 0:
            raise RuntimeError('Trivial ascent')
        profile = [DiveProfilePoint(depth,
                                    timestamp=dt.timedelta(seconds=0),
                                    consumption=configuration.consumption)]
        deep_ascent_rate = 10  # m/min
        shallow_ascent_rate = 6  # m/min
        stop_duration = 0.5  # min
        starting_depth = depth
        start_time = dt.timedelta(seconds=0)
        current_time = start_time
        if starting_depth < 3:
            current_time += dt.timedelta(minutes=starting_depth /
                                         shallow_ascent_rate)
            profile.append(DiveProfilePoint(depth=0,
                                            timestamp=current_time,
                                            consumption=configuration.consumption))
            return profile
        # Round depth to deeper 3 m
        depth = np.ceil(depth / 6) * 3.  # Half to the deeper 3 m
        current_time += dt.timedelta(minutes=(starting_depth -
                                     depth) / deep_ascent_rate)
        profile.append(DiveProfilePoint(depth=depth,
                                        timestamp=current_time,
                                        consumption=configuration.consumption))

        while depth > 0:
            # 30 second stop
            current_time += dt.timedelta(minutes=stop_duration)
            profile.append(DiveProfilePoint(depth=depth,
                                            timestamp=current_time,
                                            consumption=configuration.consumption))

            depth -= 3
            current_time += dt.timedelta(minutes=3 / shallow_ascent_rate)
            profile.append(DiveProfilePoint(depth=depth,
                                            timestamp=current_time,
                                            consumption=configuration.consumption))
        return profile
