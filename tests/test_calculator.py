import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.metrics.calculator import PerformanceMetricsCalculator

class TestMetricsCalculator(unittest.TestCase):

    def test_cop_conversion_formula(self):
        calc = PerformanceMetricsCalculator()
        
        # Test 3000W cooling over 1 hour timestep with COP=3.0 -> expected 1.0 kWh
        # Test 1000W heating over 1 hour timestep with COP=1.0 -> expected 1.0 kWh
        cooling_w = 3000.0
        heating_w = 1000.0
        
        cooling_kwh = (cooling_w / 1000.0) / calc.COOLING_COP
        heating_kwh = (heating_w / 1000.0) / calc.HEATING_COP
        
        self.assertAlmostEqual(cooling_kwh, 1.0, places=2)
        self.assertAlmostEqual(heating_kwh, 1.0, places=2)
        self.assertAlmostEqual(cooling_kwh + heating_kwh, 2.0, places=2)

if __name__ == "__main__":
    unittest.main()
