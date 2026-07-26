import csv
from typing import List

class EPWWeatherLookahead:
    """Pre-parses EPW weather file to provide lookahead outdoor temperatures."""

    def __init__(self, epw_path: str = None, synthetic_temps: List[float] = None):
        self.hourly_temps: List[float] = []
        if synthetic_temps:
            self.hourly_temps = list(synthetic_temps)
        elif epw_path:
            self._parse_epw(epw_path)
        else:
            # Default fallback 24h temperature curve
            self.hourly_temps = [15.0 + 5.0 * ((i - 6) % 24) / 18.0 for i in range(24 * 365)]

    def _parse_epw(self, epw_path: str):
        temps = []
        with open(epw_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            # Skip 8 header lines
            for _ in range(8):
                next(reader, None)
            for row in reader:
                if len(row) > 6:
                    try:
                        temp = float(row[6])
                        temps.append(temp)
                    except ValueError:
                        pass
        self.hourly_temps = temps if temps else [20.0] * (24 * 365)

    def get_lookahead(self, current_hour_index: int, hours: int = 4) -> List[float]:
        """Returns next `hours` hourly temperatures starting from `current_hour_index + 1`."""
        if not self.hourly_temps:
            return [20.0] * hours
        lookahead = []
        for offset in range(1, hours + 1):
            idx = (current_hour_index + offset) % len(self.hourly_temps)
            lookahead.append(self.hourly_temps[idx])
        return lookahead
