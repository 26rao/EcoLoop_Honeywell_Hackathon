import json
from collections import Counter
from pathlib import Path

def check_pairs():
    print("==================================================")
    print("INSPECTING SETPOINT PAIRS IN FROZEN FINAL AGENT LOG")
    print("==================================================")

    agent_path = Path("logs/FINAL_agent_event_log.jsonl")
    if not agent_path.exists():
        print(f"Error: {agent_path} missing!")
        return

    lines = open(agent_path, "r", encoding="utf-8").readlines()
    print(f"Total lines in {agent_path.name}: {len(lines)}")

    pairs = Counter()
    for line in lines:
        if not line.strip():
            continue
        r = json.loads(line)
        h = r["validation_result"]["final_heating_setpoint_c"]
        c = r["validation_result"]["final_cooling_setpoint_c"]
        pairs[(h, c)] += 1

    print(f"\nDistinct (heating, cooling) setpoint pairs used: {len(pairs)}")
    for pair, count in pairs.most_common():
        print(f"  {pair}: used {count} times")

if __name__ == "__main__":
    check_pairs()
