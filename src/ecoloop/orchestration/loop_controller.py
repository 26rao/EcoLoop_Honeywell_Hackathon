import time
from datetime import datetime
from typing import Dict, Any, Tuple
from ecoloop.state.builder import StateBuilder
from ecoloop.policy.base import SetpointPolicy
from ecoloop.safety.validator import SafetyValidator
from ecoloop.logging.event_log import EventLogger
from ecoloop.state.schema import DecisionLogRecord, Action, ValidationResult, BuildingState

class LoopController:
    """Orchestration Loop Controller: wires state building, policy decision, safety clamping, and logging."""

    def __init__(
        self,
        policy: SetpointPolicy,
        validator: SafetyValidator,
        logger: EventLogger,
        state_builder: StateBuilder,
        config: Dict[str, Any],
        is_mock_mode: bool = False
    ):
        self.policy = policy
        self.validator = validator
        self.logger = logger
        self.state_builder = state_builder
        self.config = config
        self.is_mock_mode = is_mock_mode

        self.cadence_minutes: int = config.get("decision_cadence_minutes", 60)
        self.step_counter: int = 0
        self.decision_index: int = 0

        self.current_heating_sp: float = config.get("baseline_setpoint_c", 21.0)
        self.current_cooling_sp: float = config.get("baseline_setpoint_c", 24.0)
        self.conservative_mode: bool = False

    def process_tick(
        self,
        sim_timestamp: datetime,
        sensor_readings: Dict[str, Any],
        timestep_minutes: int = 15
    ) -> Tuple[float, float]:
        """Called on each simulation timestep. Decides whether to update setpoints or hold previous."""
        self.step_counter += 1
        steps_per_decision = max(1, self.cadence_minutes // timestep_minutes)

        state: BuildingState = self.state_builder.build(
            sim_timestamp=sim_timestamp,
            zone_temps_c=sensor_readings.get("zone_temps_c", {"MainZone": 22.0}),
            pmv=sensor_readings.get("pmv", 0.0),
            occupancy_fraction=sensor_readings.get("occupancy_fraction", 1.0),
            heating_energy_rate_w=sensor_readings.get("heating_energy_rate_w", 0.0),
            cooling_energy_rate_w=sensor_readings.get("cooling_energy_rate_w", 0.0),
            outdoor_temp_c=sensor_readings.get("outdoor_temp_c", 20.0),
            current_heating_setpoint_c=self.current_heating_sp,
            current_cooling_setpoint_c=self.current_cooling_sp,
            hour_index=sensor_readings.get("hour_index", 0),
            step_hours=timestep_minutes / 60.0
        )

        if self.step_counter % steps_per_decision == 0 or self.step_counter == 1:
            start_wall_clock = time.time()

            try:
                action: Action = self.policy.decide(state)
            except Exception as e:
                self.validator.record_failure()
                action = Action(
                    heating_setpoint_c=self.current_heating_sp,
                    cooling_setpoint_c=self.current_cooling_sp,
                    rationale=f"Policy execution failed: {str(e)}. Holding setpoints."
                )

            val_result: ValidationResult = self.validator.validate(
                proposed_heating_c=action.heating_setpoint_c,
                proposed_cooling_c=action.cooling_setpoint_c,
                current_state=state,
                conservative_mode=self.conservative_mode
            )

            if val_result.accepted:
                self.validator.record_success()

            latency_s = time.time() - start_wall_clock

            self.decision_index += 1
            record = DecisionLogRecord(
                decision_index=self.decision_index,
                sim_timestamp=sim_timestamp,
                wall_clock_latency_s=round(latency_s, 4),
                policy_name=self.policy.name,
                state=state,
                proposed_action=action,
                validation_result=val_result,
                conservative_mode_active=self.conservative_mode,
                mock_mode=self.is_mock_mode
            )

            self.logger.log_decision(record)

            self.current_heating_sp = val_result.final_heating_setpoint_c
            self.current_cooling_sp = val_result.final_cooling_setpoint_c

        return self.current_heating_sp, self.current_cooling_sp
