import json
from collections import Counter
from pathlib import Path

def diagnose():
    print("==================================================")
    print("DIAGNOSING AGENT LOG: SETPOINT PAIRS & HEATING SUM")
    print("==================================================")

    agent_path = Path("logs/real_agent_event_log.jsonl")
    if not agent_path.exists():
        print(f"Error: {agent_path} does not exist!")
        return

    pairs = Counter()
    heat_sum_w = 0.0
    cool_sum_w = 0.0

    lines = open(agent_path, "r", encoding="utf-8").readlines()
    print(f"Total lines in {agent_path.name}: {len(lines)}")

    for line in lines:
        if not line.strip():
            continue
        r = json.loads(line)
        h = r["validation_result"]["final_heating_setpoint_c"]
        c = r["validation_result"]["final_cooling_setpoint_c"]
        pairs[(h, c)] += 1
        
        # Check both state and raw readings
        h_w = r["state"].get("heating_energy_rate_w", 0.0)
        c_w = r["state"].get("cooling_energy_rate_w", 0.0)
        heat_sum_w += h_w
        cool_sum_w += c_w

    print("\nDistinct (heating, cooling) setpoint pairs used:", len(pairs))
    for pair, count in pairs.most_common():
        print(f"  {pair}: used {count} times")

    print(f"\nReal summed heating energy (W): {heat_sum_w:.2f} W")
    print(f"Real summed cooling energy (W): {cool_sum_w:.2f} W")

    cool_kwh = (cool_sum_w / 1000.0) / 3.0
    heat_kwh = (heat_sum_w / 1000.0) / 1.0
    total_kwh = cool_kwh + heat_kwh

    print(f"\nDerived Electrical Energy:")
    print(f"  Cooling kWh: {cool_kwh:.2f} kWh (COP 3.0)")
    print(f"  Heating kWh: {heat_kwh:.2f} kWh (COP 1.0)")
    print(f"  Total kWh:   {total_kwh:.2f} kWh")

if __name__ == "__main__":
    diagnose()
