import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.tools.error_parser import EnergyPlusErrorParser

class TestErrorParser(unittest.TestCase):

    def test_conservative_mode_trigger(self):
        test_err_path = Path("tests/test_err_sample.err")
        with open(test_err_path, "w", encoding="utf-8") as f:
            f.write("""
Program Version,EnergyPlus, Version 24.2.0-e7ecb2d53b
 ** Warning ** Zone temperature out of bounds warning
 ** Warning ** Zone temperature out of bounds warning
 ** Warning ** High thermal discomfort detected
""")
        parser = EnergyPlusErrorParser(err_file_path=str(test_err_path))
        result = parser.parse_err_file()

        self.assertTrue(result["file_found"])
        self.assertEqual(result["warnings"], 3)
        self.assertTrue(result["conservative_mode_triggered"])

        if test_err_path.exists():
            test_err_path.unlink()

if __name__ == "__main__":
    unittest.main()
