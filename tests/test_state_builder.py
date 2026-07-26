import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.state.builder import StateBuilder

class TestStateBuilder(unittest.TestCase):

    def test_state_builder_assembly(self):
        builder = StateBuilder(history_limit=3)
        now = datetime.now(timezone.utc)

        state = builder.build(
            sim_timestamp=now,
            zone_temps_c={"MainZone": 22.5, "EastZone": 23.0},
            pmv=0.1,
            occupancy_fraction=1.0,
            heating_energy_rate_w=500.0,
            cooling_energy_rate_w=1500.0,
            outdoor_temp_c=28.0,
            current_heating_setpoint_c=21.0,
            current_cooling_setpoint_c=24.0,
            hour_index=12
        )

        self.assertEqual(state.pmv, 0.1)
        self.assertEqual(state.occupancy_fraction, 1.0)
        self.assertGreater(state.cumulative_energy_kwh, 0.0)
        self.assertEqual(len(state.lookahead_outdoor_temp_c), 4)
        self.assertEqual(len(state.thermal_history), 1)

if __name__ == "__main__":
    unittest.main()
