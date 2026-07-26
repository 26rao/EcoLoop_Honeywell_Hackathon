import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.simulation.weather_lookahead import EPWWeatherLookahead

class TestWeatherLookahead(unittest.TestCase):

    def test_weather_lookahead(self):
        synthetic_temps = [10.0 + i for i in range(24)]
        parser = EPWWeatherLookahead(synthetic_temps=synthetic_temps)

        lookahead = parser.get_lookahead(current_hour_index=5, hours=4)
        self.assertEqual(lookahead, [16.0, 17.0, 18.0, 19.0])

if __name__ == "__main__":
    unittest.main()
