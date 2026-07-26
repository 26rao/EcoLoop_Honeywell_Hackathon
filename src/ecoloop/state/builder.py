from datetime import datetime
from typing import Dict, List, Optional
from ecoloop.state.schema import BuildingState, HistoryPoint
from ecoloop.simulation.weather_lookahead import EPWWeatherLookahead

class StateBuilder:
    """Assembles complete BuildingState from runtime sensors, rolling history, and EPW lookahead."""

    def __init__(self, weather_lookahead: Optional[EPWWeatherLookahead] = None, history_limit: int = 6):
        self.weather_lookahead = weather_lookahead or EPWWeatherLookahead()
        self.history_limit = history_limit
        self.history: List[HistoryPoint] = []
        self.cumulative_energy_kwh: float = 0.0

    def add_history_point(self, timestamp: datetime, zone_temp: float, outdoor_temp: float, energy_w: float):
        point = HistoryPoint(
            sim_timestamp=timestamp,
            zone_temp_c=round(zone_temp, 2),
            outdoor_temp_c=round(outdoor_temp, 2),
            energy_rate_w=round(energy_w, 2)
        )
        self.history.append(point)
        if len(self.history) > self.history_limit:
            self.history.pop(0)

    def build(
        self,
        sim_timestamp: datetime,
        zone_temps_c: Dict[str, float],
        pmv: float,
        occupancy_fraction: float,
        heating_energy_rate_w: float,
        cooling_energy_rate_w: float,
        outdoor_temp_c: float,
        current_heating_setpoint_c: float,
        current_cooling_setpoint_c: float,
        hour_index: int = 0,
        step_hours: float = 1.0,
        carbon_intensity: float = 250.0
    ) -> BuildingState:
        # Accumulate thermal energy into kWh (W * hours / 1000)
        total_w = heating_energy_rate_w + cooling_energy_rate_w
        self.cumulative_energy_kwh += (total_w * step_hours) / 1000.0

        mean_zone_temp = sum(zone_temps_c.values()) / max(len(zone_temps_c), 1)
        self.add_history_point(sim_timestamp, mean_zone_temp, outdoor_temp_c, total_w)

        lookahead_temps = self.weather_lookahead.get_lookahead(hour_index, hours=4)

        return BuildingState(
            sim_timestamp=sim_timestamp,
            zone_temps_c={k: round(v, 2) for k, v in zone_temps_c.items()},
            pmv=round(pmv, 2),
            occupancy_fraction=round(occupancy_fraction, 2),
            heating_energy_rate_w=round(heating_energy_rate_w, 2),
            cooling_energy_rate_w=round(cooling_energy_rate_w, 2),
            outdoor_temp_c=round(outdoor_temp_c, 2),
            lookahead_outdoor_temp_c=[round(t, 2) for t in lookahead_temps],
            thermal_history=list(self.history),
            carbon_intensity_gco2_kwh=carbon_intensity,
            cumulative_energy_kwh=round(self.cumulative_energy_kwh, 3),
            current_heating_setpoint_c=round(current_heating_setpoint_c, 2),
            current_cooling_setpoint_c=round(current_cooling_setpoint_c, 2)
        )
