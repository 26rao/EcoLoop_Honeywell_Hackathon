import json
from pathlib import Path

def inspect_ticks():
    print("==================================================")
    print("INSPECTING OCCUPIED TICKS & 8:00 AM RECOVERY TRANSITIONS")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    with open(base_path, "r", encoding="utf-8") as f:
        base_records = [json.loads(l) for l in f if l.strip()]
    with open(agent_path, "r", encoding="utf-8") as f:
        agent_records = [json.loads(l) for l in f if l.strip()]

    print("\nAGENT OCCUPIED TICKS ANALYSIS (occupancy > 0):")
    non_compliant = []
    for r in agent_records:
        if r['state']['occupancy_fraction'] > 0:
            pmv = r['state']['pmv']
            t_str = r['sim_timestamp']
            idx = r['decision_index']
            temp = r['state']['zone_temps_c']['MainZone']
            cool_sp = r['validation_result']['final_cooling_setpoint_c']
            compliant = -0.5 <= pmv <= 0.5
            status = "COMPLIANT" if compliant else "NON-COMPLIANT"
            if not compliant:
                non_compliant.append((idx, t_str, temp, cool_sp, pmv))
            print(f"  Tick {idx:2d} | Time: {t_str} | ZoneTemp: {temp}°C | CoolSP: {cool_sp}°C | PMV: {pmv:+.2f} | Status: {status}")

    print("\n==================================================")
    print("NON-COMPLIANT OCCUPIED TICKS FOUND IN AGENT RUN:")
    for idx, t_str, temp, cool_sp, pmv in non_compliant:
        print(f"  -> Tick {idx} ({t_str}): ZoneTemp={temp}°C, CoolSP={cool_sp}°C, PMV={pmv:+.2f}")
    print("==================================================")

if __name__ == "__main__":
    inspect_ticks()
