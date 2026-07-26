import json
from pathlib import Path

def inspect_logs():
    print("==================================================")
    print("LOG FILE HEAD & TAIL INSPECTION VERIFICATION")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    # 1. Baseline Log Inspection
    print(f"\n1. BASELINE LOG: {base_path.name}")
    if base_path.exists():
        with open(base_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"   Total Lines: {len(lines)}")
        r_first = json.loads(lines[0])
        r_last = json.loads(lines[-1])
        print(f"   First Line (Index {r_first['decision_index']}): Policy={r_first['policy_name']} | Time={r_first['sim_timestamp']} | HeatSP={r_first['validation_result']['final_heating_setpoint_c']}°C | CoolSP={r_first['validation_result']['final_cooling_setpoint_c']}°C | CoolW={r_first['state']['cooling_energy_rate_w']}W | PMV={r_first['state']['pmv']}")
        print(f"   Last Line  (Index {r_last['decision_index']}): Policy={r_last['policy_name']} | Time={r_last['sim_timestamp']} | HeatSP={r_last['validation_result']['final_heating_setpoint_c']}°C | CoolSP={r_last['validation_result']['final_cooling_setpoint_c']}°C | CoolW={r_last['state']['cooling_energy_rate_w']}W | PMV={r_last['state']['pmv']}")

    # 2. Agent Log Inspection
    print(f"\n2. AGENT LOG: {agent_path.name}")
    if agent_path.exists():
        with open(agent_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"   Total Lines: {len(lines)}")
        r_first = json.loads(lines[0])
        r_last = json.loads(lines[-1])
        print(f"   First Line (Index {r_first['decision_index']}): Policy={r_first['policy_name']} | Time={r_first['sim_timestamp']} | HeatSP={r_first['validation_result']['final_heating_setpoint_c']}°C | CoolSP={r_first['validation_result']['final_cooling_setpoint_c']}°C | CoolW={r_first['state']['cooling_energy_rate_w']}W | PMV={r_first['state']['pmv']}")
        print(f"   Last Line  (Index {r_last['decision_index']}): Policy={r_last['policy_name']} | Time={r_last['sim_timestamp']} | HeatSP={r_last['validation_result']['final_heating_setpoint_c']}°C | CoolSP={r_last['validation_result']['final_cooling_setpoint_c']}°C | CoolW={r_last['state']['cooling_energy_rate_w']}W | PMV={r_last['state']['pmv']}")

if __name__ == "__main__":
    inspect_logs()
