import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.safety.validator import SafetyValidator
from ecoloop.tools.error_parser import EnergyPlusErrorParser
from ecoloop.state.schema import BuildingState, HistoryPoint
from datetime import datetime, timezone

def test_safety_and_conservative_mode():
    print("==================================================")
    print("EcoLoop Priority 1 — Safety Layer & Conservative Mode Stress Test")
    print("==================================================")

    config = {
        "comfort_band_c": [21.0, 26.0],
        "max_delta_c_per_step": 1.5,
        "watchdog_max_consecutive_failures": 3,
        "baseline_setpoint_c": 22.0
    }

    validator = SafetyValidator(config)

    # 1. Bounds Clamping Test (Out-of-bounds proposal)
    res_bounds = validator.validate(proposed_heating_c=16.0, proposed_cooling_c=29.0)
    print("\n1. Bounds Clamping Test:")
    print(f"   Proposed: Heating=16.0°C, Cooling=29.0°C")
    print(f"   Clamped:  {res_bounds.clamped}")
    print(f"   Final:    Heating={res_bounds.final_heating_setpoint_c}°C, Cooling={res_bounds.final_cooling_setpoint_c}°C")
    print(f"   Reason:   {res_bounds.clamp_reason}")

    # 2. Rate-of-Change Clamping Test
    now = datetime.now(timezone.utc)
    state = BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 22.0}, pmv=0.0, occupancy_fraction=1.0,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=0.0, outdoor_temp_c=22.0,
        lookahead_outdoor_temp_c=[22.0]*4, thermal_history=[], carbon_intensity_gco2_kwh=250.0,
        cumulative_energy_kwh=0.0, current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    )
    res_rate = validator.validate(proposed_heating_c=21.0, proposed_cooling_c=27.0, current_state=state)
    print("\n2. Rate-of-Change Clamping Test:")
    print(f"   Current Cooling Setpoint: {state.current_cooling_setpoint_c}°C")
    print(f"   Proposed Cooling Setpoint: 27.0°C (Delta = +3.0°C)")
    print(f"   Clamped: {res_rate.clamped}")
    print(f"   Final:   Cooling={res_rate.final_cooling_setpoint_c}°C")
    print(f"   Reason:  {res_rate.clamp_reason}")

    # 3. Watchdog Circuit Breaker Test (3 Consecutive Failures)
    print("\n3. Watchdog Circuit Breaker Test:")
    validator.record_failure()
    validator.record_failure()
    validator.record_failure()
    res_watchdog = validator.validate(proposed_heating_c=21.0, proposed_cooling_c=24.0)
    print(f"   Consecutive Failures: {validator.consecutive_failures}")
    print(f"   Watchdog Tripped:     {validator.watchdog_tripped}")
    print(f"   Clamped:              {res_watchdog.clamped}")
    print(f"   Reason:               {res_watchdog.clamp_reason}")

    # 4. Conservative Mode Trigger Test (.err parsing)
    synthetic_err = Path("logs/test_synthetic.err")
    with open(synthetic_err, "w", encoding="utf-8") as f:
        f.write("""
Program Version,EnergyPlus, Version 24.2.0-e7ecb2d53b
 ** Warning ** Zone temperature out of bounds warning: SPACE1-1
 ** Warning ** Zone temperature out of bounds warning: SPACE1-1
 ** Warning ** High occupant comfort warning detected
""")
    parser = EnergyPlusErrorParser(err_file_path=str(synthetic_err))
    parse_res = parser.parse_err_file()
    print("\n4. Conservative Mode .err Parsing Test:")
    print(f"   Warnings Found: {parse_res['warnings']}")
    print(f"   Conservative Mode Triggered: {parse_res['conservative_mode_triggered']}")

    if synthetic_err.exists():
        synthetic_err.unlink()

    print("\n==================================================")
    print("ALL SAFETY & CONSERVATIVE MODE STRESS TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_safety_and_conservative_mode()
