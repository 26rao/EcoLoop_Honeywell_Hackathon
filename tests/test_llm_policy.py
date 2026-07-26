import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.policy.llm_policy import LLMAgentPolicy
from ecoloop.state.schema import BuildingState, Action

class TestLLMAgentPolicy(unittest.TestCase):

    def setUp(self):
        self.config = {
            "ollama_url": "http://localhost:11434/api/chat",
            "llm_model_name": "qwen2.5:7b-instruct",
            "llm_timeout_s": 35,
            "llm_max_retries": 2
        }
        self.policy = LLMAgentPolicy(self.config)

    def test_prompt_construction(self):
        state = BuildingState(
            sim_timestamp=datetime.now(timezone.utc),
            zone_temps_c={"MainZone": 22.0}, pmv=0.0, occupancy_fraction=1.0,
            heating_energy_rate_w=0.0, cooling_energy_rate_w=0.0, outdoor_temp_c=22.0,
            lookahead_outdoor_temp_c=[22.0]*4, thermal_history=[], carbon_intensity_gco2_kwh=250.0,
            cumulative_energy_kwh=0.0, current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
        )
        prompt = self.policy._build_prompt(state)
        self.assertIn("OCCUPIED", prompt)
        self.assertIn("MainZone", prompt)

    @patch("ecoloop.policy.llm_policy.LLMAgentPolicy._call_ollama")
    def test_decide_canned_response(self, mock_ollama):
        mock_ollama.return_value = ({
            "heating_setpoint_c": 21.0,
            "cooling_setpoint_c": 24.0,
            "rationale": "Canned unit test optimization rationale"
        }, 1.5)

        state = BuildingState(
            sim_timestamp=datetime.now(timezone.utc),
            zone_temps_c={"MainZone": 22.0}, pmv=0.0, occupancy_fraction=1.0,
            heating_energy_rate_w=0.0, cooling_energy_rate_w=0.0, outdoor_temp_c=22.0,
            lookahead_outdoor_temp_c=[22.0]*4, thermal_history=[], carbon_intensity_gco2_kwh=250.0,
            cumulative_energy_kwh=0.0, current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
        )

        action = self.policy.decide(state)
        self.assertEqual(action.heating_setpoint_c, 21.0)
        self.assertEqual(action.cooling_setpoint_c, 24.0)
        self.assertIn("Canned unit test", action.rationale)

if __name__ == "__main__":
    unittest.main()
