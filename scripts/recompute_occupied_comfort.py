import json
from pathlib import Path

def compute_occupied_comfort():
    print("==================================================")
    print("OCCUPIED-HOURS PMV THERMAL COMFORT COMPLIANCE CHECK")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    def analyze_log(path, name):
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    records.append(json.loads(l))

        all_pmv = [r['state']['pmv'] for r in records]
        occ_pmv = [r['state']['pmv'] for r in records if r['state']['occupancy_fraction'] > 0]
        unocc_pmv = [r['state']['pmv'] for r in records if r['state']['occupancy_fraction'] == 0]

        all_compliant = sum(1 for p in all_pmv if -0.5 <= p <= 0.5)
        occ_compliant = sum(1 for p in occ_pmv if -0.5 <= p <= 0.5)

        all_pct = (all_compliant / len(all_pmv)) * 100.0 if all_pmv else 0
        occ_pct = (occ_compliant / len(occ_pmv)) * 100.0 if occ_pmv else 0

        print(f"\n{name} ({path.name}):")
        print(f"  Total Records: {len(records)} | Occupied Ticks: {len(occ_pmv)} | Unoccupied Ticks: {len(unocc_pmv)}")
        print(f"  All-Hours PMV Compliance:       {all_pct:.1f}% (PMV range: [{min(all_pmv)}, {max(all_pmv)}])")
        print(f"  OCCUPIED-HOURS PMV Compliance:  {occ_pct:.1f}% (PMV range: [{min(occ_pmv)}, {max(occ_pmv)}], Mean: {sum(occ_pmv)/len(occ_pmv):.2f})")
        print(f"  Unoccupied-Hours PMV Range:     [{min(unocc_pmv)}, {max(unocc_pmv)}]")

        return occ_pct, all_pct

    b_occ, b_all = analyze_log(base_path, "LEGACY BASELINE POLICY")
    a_occ, a_all = analyze_log(agent_path, "AUTONOMOUS LLM AGENT")

    print("\n==================================================")
    print("FINAL SUMMARY COMPARISON:")
    print(f"  - Baseline Occupied Comfort Compliance: {b_occ:.1f}%")
    print(f"  - Agent Occupied Comfort Compliance:    {a_occ:.1f}%")
    print("==================================================")

if __name__ == "__main__":
    compute_occupied_comfort()
