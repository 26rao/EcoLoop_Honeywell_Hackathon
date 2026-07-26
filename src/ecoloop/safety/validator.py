from typing import Tuple, Dict, Any, Optional
from ecoloop.state.schema import ValidationResult, BuildingState

class SafetyValidator:
    """Single source of truth for safety validation, bounds clamping, rate-of-change limits, and watchdog circuit breaker."""

    def __init__(self, config: Dict[str, Any]):
        self.comfort_band: Tuple[float, float] = tuple(config.get("comfort_band_c", [21.0, 26.0]))
        self.max_delta_c: float = config.get("max_delta_c_per_step", 1.5)
        self.max_failures: int = config.get("watchdog_max_consecutive_failures", 3)
        self.baseline_setpoint: float = config.get("baseline_setpoint_c", 22.0)
        self.min_deadband_c: float = config.get("min_deadband_c", 1.0)
        self.consecutive_failures: int = 0
        self.watchdog_tripped: bool = False

    def reset_watchdog(self):
        self.consecutive_failures = 0
        self.watchdog_tripped = False

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_failures:
            self.watchdog_tripped = True

    def record_success(self):
        self.consecutive_failures = 0

    def validate(
        self,
        proposed_heating_c: float,
        proposed_cooling_c: float,
        current_state: Optional[BuildingState] = None,
        conservative_mode: bool = False
    ) -> ValidationResult:
        # If watchdog tripped, force safe baseline
        if self.watchdog_tripped:
            return ValidationResult(
                accepted=False,
                final_heating_setpoint_c=self.baseline_setpoint,
                final_cooling_setpoint_c=self.baseline_setpoint + self.min_deadband_c,
                clamped=True,
                clamp_reason="Watchdog circuit breaker tripped! Freezing to safe baseline.",
                watchdog_tripped=True
            )

        # Comfort band bounds: overall upper/lower boundaries
        min_temp, max_temp = self.comfort_band
        if conservative_mode:
            min_temp += 0.5
            max_temp -= 0.5

        clamped = False
        reasons = []

        final_heating = proposed_heating_c
        final_cooling = proposed_cooling_c

        # 1. Bounds check (allow heating down to 18.0C during unoccupied setback)
        if final_heating < 18.0:
            final_heating = 18.0
            clamped = True
            reasons.append(f"Heating setpoint {proposed_heating_c}°C below absolute min 18.0°C")
        elif final_heating > max_temp - self.min_deadband_c:
            final_heating = max_temp - self.min_deadband_c
            clamped = True
            reasons.append(f"Heating setpoint {proposed_heating_c}°C above max allowed {max_temp - self.min_deadband_c}°C")

        if final_cooling > max_temp:
            final_cooling = max_temp
            clamped = True
            reasons.append(f"Cooling setpoint {proposed_cooling_c}°C above max comfort {max_temp}°C")
        elif final_cooling < min_temp:
            final_cooling = min_temp
            clamped = True
            reasons.append(f"Cooling setpoint {proposed_cooling_c}°C below min comfort {min_temp}°C")

        # 2. Strict Deadband Check: Enforce cooling_setpoint >= heating_setpoint + min_deadband
        if final_cooling < final_heating + self.min_deadband_c:
            final_cooling = final_heating + self.min_deadband_c
            clamped = True
            reasons.append(f"Deadband constraint enforced: cooling ({final_cooling}°C) must be >= heating ({final_heating}°C) + {self.min_deadband_c}°C")

        # 3. Rate of change limits (if current state available)
        if current_state:
            prev_heating = current_state.current_heating_setpoint_c
            prev_cooling = current_state.current_cooling_setpoint_c

            if abs(final_heating - prev_heating) > self.max_delta_c:
                delta = self.max_delta_c if final_heating > prev_heating else -self.max_delta_c
                final_heating = prev_heating + delta
                clamped = True
                reasons.append(f"Heating rate of change exceeded limit {self.max_delta_c}°C/step")

            if abs(final_cooling - prev_cooling) > self.max_delta_c:
                delta = self.max_delta_c if final_cooling > prev_cooling else -self.max_delta_c
                final_cooling = prev_cooling + delta
                clamped = True
                reasons.append(f"Cooling rate of change exceeded limit {self.max_delta_c}°C/step")

        return ValidationResult(
            accepted=not clamped,
            final_heating_setpoint_c=round(final_heating, 2),
            final_cooling_setpoint_c=round(final_cooling, 2),
            clamped=clamped,
            clamp_reason="; ".join(reasons) if reasons else None,
            watchdog_tripped=False
        )
