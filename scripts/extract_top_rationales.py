import json
from pathlib import Path

def extract_rationales():
    print("==================================================")
    print("EXTRACTING REAL LLM RATIONALE QUOTES FROM AGENT LOG")
    print("==================================================")

    agent_path = Path("logs/real_agent_event_log.jsonl")
    with open(agent_path, "r", encoding="utf-8") as f:
        records = [json.loads(l) for l in f if l.strip()]

    print(f"Total Logged Rationales: {len(records)}\n")
    
    # Filter diverse rationales (unoccupied setback, occupied comfort, weather lookahead)
    selected = [
        records[0],   # Midnight unoccupied setback (Tick 1)
        records[9],   # 8:00 AM Occupancy transition (Tick 10)
        records[20],  # Midday peak (Tick 21)
    ]

    for idx, r in enumerate(selected, 1):
        print(f"Quote {idx} (Tick {r['decision_index']} - {r['sim_timestamp']}):")
        print(f"  Policy:    {r['policy_name']}")
        print(f"  Occupancy: {r['state']['occupancy_fraction']} (PMV: {r['state']['pmv']}, Outdoor Temp: {r['state']['outdoor_temp_c']}°C)")
        print(f"  Setpoints: Heating={r['validation_result']['final_heating_setpoint_c']}°C | Cooling={r['validation_result']['final_cooling_setpoint_c']}°C")
        print(f"  Rationale: \"{r['proposed_action']['rationale']}\"\n")

if __name__ == "__main__":
    extract_rationales()
