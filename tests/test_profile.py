'''Tests the dive profile
'''
import math

from dive_profile_calculator.profile import DiveProfile


def test_depth_calculation():
    """Verifies the seawater depth calculations.
    """
    profile = DiveProfile(
        gas_volume=12.0,
        gas_pressure=232,
        profile=[],
        gravity_constant=9.80665,
        water_density=1023.6
    )
    assert math.isclose(profile.ambient_pressure(0), 1)
    assert math.isclose(profile.ambient_pressure(9.962057571), 2)
    assert math.isclose(profile.ambient_pressure(10), 2.003808694)
    assert math.isclose(profile.ambient_pressure(20), 3.007617388)
    assert math.isclose(profile.ambient_pressure(30), 4.011426082)
    assert math.isclose(profile.ambient_pressure(40), 5.015234776)
    assert math.isclose(profile.ambient_pressure(50), 6.01904347)

def test_load_profile():
    """Tests loading profiles
    """
    gas_pressure = 232
    gas_volume = 12
    data = {
        'gas_volume': gas_volume,
        'gas_pressure': gas_pressure,
        'profile': {
            0: {
                'depth': 0,
                'consumption': 15
            },
            60: {
                'depth': 10,
                'consumption': 15
            },
            120: {
                'depth': 0,
                'consumption': 15
            }
        }
    }
    profile = DiveProfile.from_dict(data)
    assert math.isclose(profile.gas_pressure, gas_pressure)
    assert math.isclose(profile.gas_volume, gas_volume)
