from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class HistoryPoint(BaseModel):
    sim_timestamp: datetime
    zone_temp_c: float
    outdoor_temp_c: float
    energy_rate_w: float

class BuildingState(BaseModel):
    sim_timestamp: datetime
    zone_temps_c: Dict[str, float]
    pmv: float
    occupancy_fraction: float
    heating_energy_rate_w: float
    cooling_energy_rate_w: float
    outdoor_temp_c: float
    lookahead_outdoor_temp_c: List[float]
    thermal_history: List[HistoryPoint]
    carbon_intensity_gco2_kwh: float
    cumulative_energy_kwh: float
    current_heating_setpoint_c: float
    current_cooling_setpoint_c: float

class Action(BaseModel):
    heating_setpoint_c: float
    cooling_setpoint_c: float
    rationale: str
    latency_s: Optional[float] = None

class ValidationResult(BaseModel):
    accepted: bool
    final_heating_setpoint_c: float
    final_cooling_setpoint_c: float
    clamped: bool
    clamp_reason: Optional[str] = None
    watchdog_tripped: bool = False

class DecisionLogRecord(BaseModel):
    decision_index: int
    sim_timestamp: datetime
    wall_clock_latency_s: float
    policy_name: str
    state: BuildingState
    proposed_action: Action
    validation_result: ValidationResult
    conservative_mode_active: bool = False
    mock_mode: bool = False
