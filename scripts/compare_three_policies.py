import json
from pathlib import Path

def compare_three_policies():
    print("==================================================")
    print("THREE-POLICY EMPIRICAL COMPARISON BENCHMARK")
    print("==================================================")

    p_base = Path("logs/real_baseline_event_log.jsonl")
    p_timer = Path("logs/real_timer_event_log.jsonl")
    p_agent = Path("logs/real_agent_event_log.jsonl")

    def calc_policy(path, name):
        with open(path, "r", encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]

        cool_wh = sum(r['state']['cooling_energy_rate_w'] for r in records)
        heat_wh = sum(r['state']['heating_energy_rate_w'] for r in records)

        cool_kwh = (cool_wh / 1000.0) / 3.0
        heat_kwh = (heat_wh / 1000.0) / 1.0
        total_kwh = cool_kwh + heat_kwh

        all_pmvs = [r['state']['pmv'] for r in records]
        occ_pmvs = [r['state']['pmv'] for r in records if r['state']['occupancy_fraction'] > 0]
        unocc_pmvs = [r['state']['pmv'] for r in records if r['state']['occupancy_fraction'] == 0]

        occ_compliant = sum(1 for p in occ_pmvs if -0.5 <= p <= 0.5)
        occ_comfort_pct = (occ_compliant / len(occ_pmvs)) * 100.0 if occ_pmvs else 0.0

        print(f"\n{name} ({path.name}):")
        print(f"  Records: {len(records)} | Occupied Ticks: {len(occ_pmvs)}")
        print(f"  Cooling kWh: {cool_kwh:.2f} | Heating kWh: {heat_kwh:.2f} | Total: {total_kwh:.2f} kWh")
        print(f"  Occupied PMV Compliance: {occ_comfort_pct:.1f}% (Range: [{min(occ_pmvs)}, {max(occ_pmvs)}])")

        return total_kwh, occ_comfort_pct

    b_kwh, b_pct = calc_policy(p_base, "1. LEGACY FLAT BEMS BASELINE")
    t_kwh, t_pct = calc_policy(p_timer, "2. PROGRAMMABLE SETBACK TIMER")
    a_kwh, a_pct = calc_policy(p_agent, "3. AUTONOMOUS LLM AGENT (qwen2.5)")

    t_sav = ((b_kwh - t_kwh) / b_kwh) * 100.0
    a_sav = ((b_kwh - a_kwh) / b_kwh) * 100.0
    agent_over_timer = ((t_kwh - a_kwh) / t_kwh) * 100.0

    print("\n==================================================")
    print("BENCHMARK COMPARISON SUMMARY:")
    print(f"  - Baseline Total kWh:        {b_kwh:.2f} kWh  (100.0%) | Occupied PMV: {b_pct:.1f}%")
    print(f"  - Programmable Timer kWh:    {t_kwh:.2f} kWh  (-{t_sav:.1f}% vs Flat) | Occupied PMV: {t_pct:.1f}%")
    print(f"  - Autonomous LLM Agent kWh:  {a_kwh:.2f} kWh  (-{a_sav:.1f}% vs Flat) | Occupied PMV: {a_pct:.1f}%")
    print(f"  - LLM Agent Incremental Savings over Programmable Timer: -{agent_over_timer:.2f}% ({round(t_kwh - a_kwh, 2)} kWh)")
    print("==================================================")

if __name__ == "__main__":
    compare_three_policies()
