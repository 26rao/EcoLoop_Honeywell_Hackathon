import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.safety.validator import SafetyValidator
from datetime import datetime, timezone
from ecoloop.state.schema import BuildingState

class TestSafetyValidator(unittest.TestCase):

    def test_comfort_band_clamping(self):
        config = {"comfort_band_c": [21.0, 26.0], "max_delta_c_per_step": 2.0}
        validator = SafetyValidator(config)

        res = validator.validate(proposed_heating_c=16.0, proposed_cooling_c=25.0)
        self.assertTrue(res.clamped)
        self.assertEqual(res.final_heating_setpoint_c, 18.0)

        res2 = validator.validate(proposed_heating_c=22.0, proposed_cooling_c=28.0)
        self.assertTrue(res2.clamped)
        self.assertEqual(res2.final_cooling_setpoint_c, 26.0)

    def test_rate_of_change_clamping(self):
        config = {"comfort_band_c": [18.0, 30.0], "max_delta_c_per_step": 1.5}
        validator = SafetyValidator(config)

        state = BuildingState(
            sim_timestamp=datetime.now(timezone.utc),
            zone_temps_c={"MainZone": 22.0},
            pmv=0.0,
            occupancy_fraction=1.0,
            heating_energy_rate_w=0.0,
            cooling_energy_rate_w=0.0,
            outdoor_temp_c=20.0,
            lookahead_outdoor_temp_c=[20.0, 20.0, 20.0, 20.0],
            thermal_history=[],
            carbon_intensity_gco2_kwh=200.0,
            cumulative_energy_kwh=10.0,
            current_heating_setpoint_c=20.0,
            current_cooling_setpoint_c=24.0
        )

        res = validator.validate(proposed_heating_c=23.0, proposed_cooling_c=24.5, current_state=state)
        self.assertTrue(res.clamped)
        self.assertEqual(res.final_heating_setpoint_c, 21.5)

    def test_watchdog_circuit_breaker(self):
        config = {"watchdog_max_consecutive_failures": 2, "baseline_setpoint_c": 22.0}
        validator = SafetyValidator(config)

        validator.record_failure()
        self.assertFalse(validator.watchdog_tripped)

        validator.record_failure()
        self.assertTrue(validator.watchdog_tripped)

        res = validator.validate(proposed_heating_c=25.0, proposed_cooling_c=25.5)
        self.assertTrue(res.watchdog_tripped)
        self.assertEqual(res.final_heating_setpoint_c, 22.0)

if __name__ == "__main__":
    unittest.main()
