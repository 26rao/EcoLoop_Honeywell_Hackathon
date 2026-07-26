from ecoloop.state.schema import BuildingState, Action

class FixedSchedulePolicy:
    """Phase 1 Legacy Flat Baseline Policy: constant 21°C heating / 24°C cooling 24/7 without night setback."""

    name: str = "fixed_schedule"

    def __init__(self, default_heating_c: float = 21.0, default_cooling_c: float = 24.0):
        self.default_heating_c = default_heating_c
        self.default_cooling_c = default_cooling_c

    def decide(self, state: BuildingState) -> Action:
        heating = self.default_heating_c
        cooling = self.default_cooling_c
        rationale = f"Legacy BEMS flat schedule. Constant setpoints {heating}°C heating / {cooling}°C cooling 24/7."

        return Action(
            heating_setpoint_c=heating,
            cooling_setpoint_c=cooling,
            rationale=rationale
        )

class RuleSetbackPolicy:
    """Programmable Thermostat Proxy: fixed rule-based schedule (heating 21°C/cooling 24°C occupied, heating 18°C/cooling 26°C unoccupied)."""

    name: str = "rule_setback_timer"

    def __init__(self, occ_heating_c: float = 21.0, occ_cooling_c: float = 24.0, unocc_heating_c: float = 18.0, unocc_cooling_c: float = 26.0):
        self.occ_heating_c = occ_heating_c
        self.occ_cooling_c = occ_cooling_c
        self.unocc_heating_c = unocc_heating_c
        self.unocc_cooling_c = unocc_cooling_c

    def decide(self, state: BuildingState) -> Action:
        if state.occupancy_fraction > 0.0:
            heating = self.occ_heating_c
            cooling = self.occ_cooling_c
            rationale = f"Programmable Timer Occupied. Comfort setpoints {heating}°C heating / {cooling}°C cooling."
        else:
            heating = self.unocc_heating_c
            cooling = self.unocc_cooling_c
            rationale = f"Programmable Timer Unoccupied Setback. Energy-saving setpoints {heating}°C heating / {cooling}°C cooling."

        return Action(
            heating_setpoint_c=heating,
            cooling_setpoint_c=cooling,
            rationale=rationale
        )
