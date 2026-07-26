import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, r"C:\EnergyPlusV24-2-0")

from pyenergyplus.api import EnergyPlusAPI
from ecoloop.orchestration.loop_controller import LoopController
from ecoloop.policy.llm_policy import LLMAgentPolicy
from ecoloop.safety.validator import SafetyValidator
from ecoloop.logging.event_log import EventLogger
from ecoloop.state.builder import StateBuilder
from ecoloop.simulation.weather_lookahead import EPWWeatherLookahead

def run_agent_test():
    print("==================================================")
    print("EXECUTING GENUINE SECOND INDEPENDENT LLM AGENT RUN")
    print("==================================================")

    config_path = project_root / "config" / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    idf_file = str(project_root / "models" / "agent_ready.idf")
    epw_file = str(project_root / "weather" / "location.epw")
    out_dir = str(project_root / "logs" / "test_run2_ep_out")
    log_path = project_root / "logs" / "real_agent_event_log_run2.jsonl"

    policy = LLMAgentPolicy(config)
    policy.warmup()

    validator = SafetyValidator(config)
    logger = EventLogger(log_file_path=str(log_path))

    weather_lookahead = EPWWeatherLookahead(epw_path=epw_file)
    state_builder = StateBuilder(weather_lookahead=weather_lookahead)

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

    def callback_function(s):
        if not api.exchange.api_data_fully_ready(s):
            return

        if api.exchange.warmup_flag(s):
            return

        if "temp" not in handles:
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

        heat_sp, cool_sp = controller.process_tick(sim_time, readings, timestep_minutes=15)

        api.exchange.set_actuator_value(s, handles["heat_sp"], heat_sp)
        api.exchange.set_actuator_value(s, handles["cool_sp"], cool_sp)

    api.runtime.callback_begin_zone_timestep_before_init_heat_balance(state_arg, callback_function)

    cmd_args = ["-d", out_dir, "-w", epw_file, idf_file]
    start_time = time.time()
    print("Executing second independent LLM agent simulation run...")
    exit_code = api.runtime.run_energyplus(state_arg, cmd_args)
    elapsed = time.time() - start_time

    print("\n==================================================")
    print("Second LLM Agent Simulation Run Complete!")
    print(f"- Exit Code: {exit_code}")
    print(f"- Wall-Clock Time: {elapsed:.2f}s ({elapsed/60:.2f} min)")
    print(f"- Decisions Logged: {controller.decision_index}")
    print(f"- Log Path: {log_path}")
    print("==================================================")

if __name__ == "__main__":
    run_agent_test()
