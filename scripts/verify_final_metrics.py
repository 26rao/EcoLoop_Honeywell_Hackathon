import json
from pathlib import Path

def verify_final_metrics():
    print("==================================================")
    print("ECOLOOP FINAL TRUTH EXTRACTION & METRIC VERIFICATION")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    if not base_path.exists() or not agent_path.exists():
        print("Error: Event log files missing!")
        return

    with open(base_path, "r", encoding="utf-8") as f:
        base_records = [json.loads(l) for l in f if l.strip()]

    with open(agent_path, "r", encoding="utf-8") as f:
        agent_records = [json.loads(l) for l in f if l.strip()]

    def summarize_records(records, name):
        first_ts = records[0]["sim_timestamp"]
        last_ts = records[-1]["sim_timestamp"]
        count = len(records)

        cool_wh = sum(r["state"]["cooling_energy_rate_w"] for r in records)
        heat_wh = sum(r["state"]["heating_energy_rate_w"] for r in records)

        cool_kwh = (cool_wh / 1000.0) / 3.0
        heat_kwh = (heat_wh / 1000.0) / 1.0
        total_kwh = cool_kwh + heat_kwh

        all_pmv = [r["state"]["pmv"] for r in records]
        occ_pmv = [r["state"]["pmv"] for r in records if r["state"].get("occupancy_fraction", 1.0) > 0]

        avg_pmv = sum(all_pmv) / len(all_pmv)
        all_comfort_pct = (sum(1 for p in all_pmv if -0.5 <= p <= 0.5) / len(all_pmv)) * 100.0
        occ_comfort_pct = (sum(1 for p in occ_pmv if -0.5 <= p <= 0.5) / len(occ_pmv)) * 100.0 if occ_pmv else 0.0

        print(f"\n{name}:")
        print(f"  First timestamp:       {first_ts}")
        print(f"  Last timestamp:        {last_ts}")
        print(f"  Number of decisions:   {count}")
        print(f"  Total energy:          {total_kwh:.2f} kWh (Cooling: {cool_kwh:.2f} kWh, Heating: {heat_kwh:.2f} kWh)")
        print(f"  Avg PMV:               {avg_pmv:+.2f} (Range: [{min(all_pmv):+.2f}, {max(all_pmv):+.2f}])")
        print(f"  All-hours comfort %:   {all_comfort_pct:.1f}%")
        print(f"  Occupied comfort %:    {occ_comfort_pct:.1f}%")

        return total_kwh, occ_comfort_pct

    b_kwh, b_comfort = summarize_records(base_records, "BASELINE")
    a_kwh, a_comfort = summarize_records(agent_records, "AGENT")

    print("\n--------------------------------------------------")
    print("DECISION DIFFERENCES COMPARISON:")
    diff_count = 0
    total_ticks = min(len(base_records), len(agent_records))

    for i in range(total_ticks):
        b_r = base_records[i]
        a_r = agent_records[i]

        b_heat = b_r["validation_result"]["final_heating_setpoint_c"]
        b_cool = b_r["validation_result"]["final_cooling_setpoint_c"]
        a_heat = a_r["validation_result"]["final_heating_setpoint_c"]
        a_cool = a_r["validation_result"]["final_cooling_setpoint_c"]

        if b_heat != a_heat or b_cool != a_cool:
            diff_count += 1
            print(f"  Tick {b_r['decision_index']:2d} ({b_r['sim_timestamp']}): Baseline [H={b_heat}°C, C={b_cool}°C] vs Agent [H={a_heat}°C, C={a_cool}°C]")

    print("--------------------------------------------------")
    print(f"Different setpoint decisions: {diff_count}/{total_ticks} ticks")
    savings_pct = ((b_kwh - a_kwh) / b_kwh) * 100.0
    print(f"Verified Electrical Savings: {savings_pct:.2f}% ({b_kwh:.2f} kWh baseline vs {a_kwh:.2f} kWh agent)")
    print("==================================================")

if __name__ == "__main__":
    verify_final_metrics()
