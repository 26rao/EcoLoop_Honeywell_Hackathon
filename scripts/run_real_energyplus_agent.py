import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add EnergyPlus install dir and src dir to path
sys.path.insert(0, r"C:\EnergyPlusV24-2-0")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenergyplus.api import EnergyPlusAPI
from ecoloop.policy.llm_policy import LLMAgentPolicy
from ecoloop.safety.validator import SafetyValidator
from ecoloop.logging.event_log import EventLogger
from ecoloop.state.builder import StateBuilder
from ecoloop.orchestration.loop_controller import LoopController

def run_real_energyplus_agent():
    print("==================================================")
    print("EcoLoop Phase 2 — REAL EnergyPlus Closed-Loop LLM Agent Execution")
    print("==================================================")

    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    log_path = Path("logs/real_agent_event_log.jsonl")
    if log_path.exists():
        log_path.unlink()

    policy = LLMAgentPolicy(config)
    policy.warmup()  # Load qwen2.5 model into memory before simulation start

    validator = SafetyValidator(config)
    logger = EventLogger(log_file_path=str(log_path))
    state_builder = StateBuilder()

    controller = LoopController(
        policy=policy,
        validator=validator,
        logger=logger,
        state_builder=state_builder,
        config=config,
        is_mock_mode=False
    )

    api = EnergyPlusAPI()
    state_arg = api.state_manager.new_state()

    handles = {}
    total_start_wall_time = time.time()

    def callback_function(s):
        if not api.exchange.api_data_fully_ready(s):
            return

        # Skip warmup days so decision ticks map 1:1 to the 72-hour RunPeriod
        if api.exchange.warmup_flag(s):
            return

        if "temp" not in handles:
            handles["temp"] = api.exchange.get_variable_handle(s, "Zone Air System Sensible Heating Rate", "SPACE1-1")
            handles["temp"] = api.exchange.get_variable_handle(s, "Zone Air Temperature", "SPACE1-1")
            handles["pmv"] = api.exchange.get_variable_handle(s, "Zone Thermal Comfort Fanger Model PMV", "SPACE1-1 People 1")
            handles["heat_rate"] = api.exchange.get_variable_handle(s, "Zone Air System Sensible Heating Rate", "SPACE1-1")
            handles["cool_rate"] = api.exchange.get_variable_handle(s, "Zone Air System Sensible Cooling Rate", "SPACE1-1")
            handles["heat_sp"] = api.exchange.get_actuator_handle(s, "Zone Temperature Control", "Heating Setpoint", "SPACE1-1")
            handles["cool_sp"] = api.exchange.get_actuator_handle(s, "Zone Temperature Control", "Cooling Setpoint", "SPACE1-1")

        zone_temp = api.exchange.get_variable_value(s, handles["temp"])
        pmv_val = api.exchange.get_variable_value(s, handles["pmv"])
        heat_w = api.exchange.get_variable_value(s, handles["heat_rate"])
        cool_w = api.exchange.get_variable_value(s, handles["cool_rate"])

        day = api.exchange.day_of_month(s)
        hour = api.exchange.current_time(s)
        sim_time = datetime(2015, 7, day if day > 0 else 7, int(hour) % 24, 0, tzinfo=timezone.utc)

        readings = {
            "zone_temps_c": {"MainZone": round(zone_temp, 2)},
            "pmv": round(pmv_val, 2),
            "occupancy_fraction": 1.0 if 8 <= hour < 18 else 0.0,
            "heating_energy_rate_w": max(0.0, round(heat_w, 2)),
            "cooling_energy_rate_w": max(0.0, round(cool_w, 2)),
            "outdoor_temp_c": 22.0,
            "hour_index": int(hour)
        }

        heat_set, cool_set = controller.process_tick(sim_time, readings, timestep_minutes=15)

        api.exchange.set_actuator_value(s, handles["heat_sp"], heat_set)
        api.exchange.set_actuator_value(s, handles["cool_sp"], cool_set)

    api.runtime.callback_begin_zone_timestep_before_init_heat_balance(state_arg, callback_function)

    cmd_args = [
        "-d", "logs/real_agent_ep_out",
        "-w", "weather/location.epw",
        "models/agent_ready.idf"
    ]

    print("Executing real LLM Agent closed-loop EnergyPlus simulation...")
    exit_code = api.runtime.run_energyplus(state_arg, cmd_args)
    api.state_manager.delete_state(state_arg)

    elapsed_wall_time = time.time() - total_start_wall_time
    records = logger.read_all_records()

    print(f"\n==================================================")
    print(f"Real EnergyPlus LLM Agent Execution Complete!")
    print(f"- Exit Code: {exit_code}")
    print(f"- Total Wall-Clock Time: {round(elapsed_wall_time, 2)}s ({round(elapsed_wall_time/60, 2)} minutes)")
    print(f"- Total Decisions Logged: {len(records)}")
    print(f"- Output directory: logs/real_agent_ep_out")
    print(f"==================================================")

if __name__ == "__main__":
    run_real_energyplus_agent()
