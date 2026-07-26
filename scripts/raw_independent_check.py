import json

def summarize(path):
    cool_w, heat_w, occ_cool_w, unocc_cool_w = [], [], [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            s = r["state"]
            cool_w.append(s["cooling_energy_rate_w"])
            heat_w.append(s.get("heating_energy_rate_w", 0.0))
            occ = s.get("occupancy_fraction", 1.0)
            if occ > 0:
                occ_cool_w.append(s["cooling_energy_rate_w"])
            else:
                unocc_cool_w.append(s["cooling_energy_rate_w"])

    cool_kwh = sum(cool_w) / 3000.0   # COP 3.0
    heat_kwh = sum(heat_w) / 1000.0   # COP 1.0
    total_kwh = cool_kwh + heat_kwh

    print(f"{path}")
    print(f"  records: {len(cool_w)}")
    print(f"  cooling kWh: {cool_kwh:.2f} | heating kWh: {heat_kwh:.2f} | total: {total_kwh:.2f}")
    print(f"  occupied-hours cooling sum (W): {sum(occ_cool_w):.1f}")
    print(f"  unoccupied-hours cooling sum (W): {sum(unocc_cool_w):.1f}")

if __name__ == "__main__":
    print("==================================================")
    print("INDEPENDENT RAW LOG CHECK & OCCUPIED/UNOCCUPIED BREAKDOWN")
    print("==================================================")
    summarize("logs/real_baseline_event_log.jsonl")
    print("--------------------------------------------------")
    summarize("logs/real_agent_event_log.jsonl")
