import json
from pathlib import Path

def compare_ticks():
    print("==================================================")
    print("SIDE-BY-SIDE OCCUPIED TICKS BOOLEAN COMPLIANCE DIFF")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    with open(base_path, "r", encoding="utf-8") as f:
        base_records = [json.loads(l) for l in f if l.strip()]
    with open(agent_path, "r", encoding="utf-8") as f:
        agent_records = [json.loads(l) for l in f if l.strip()]

    base_occ = [r for r in base_records if r['state']['occupancy_fraction'] > 0]
    agent_occ = [r for r in agent_records if r['state']['occupancy_fraction'] > 0]

    print(f"Total Occupied Ticks: Baseline={len(base_occ)}, Agent={len(agent_occ)}\n")
    print(f"{'OccIndex':<9} | {'Sim Timestamp':<20} | {'Base PMV':<9} | {'Base OK':<7} | {'Agent PMV':<9} | {'Agent OK':<8} | {'Diff Note'}")
    print("-" * 90)

    base_failures = []
    agent_failures = []
    diff_ticks = []

    for i in range(min(len(base_occ), len(agent_occ))):
        b_r = base_occ[i]
        a_r = agent_occ[i]

        b_pmv = b_r['state']['pmv']
        a_pmv = a_r['state']['pmv']

        b_ok = -0.5 <= b_pmv <= 0.5
        a_ok = -0.5 <= a_pmv <= 0.5

        t_str = b_r['sim_timestamp']
        idx = b_r['decision_index']

        if not b_ok:
            base_failures.append(idx)
        if not a_ok:
            agent_failures.append(idx)

        note = ""
        if b_ok != a_ok:
            diff_ticks.append(idx)
            note = "<-- DIFFERENT"

        print(f"Tick {idx:<4} | {t_str:<20} | {b_pmv:+.2f}     | {str(b_ok):<7} | {a_pmv:+.2f}      | {str(a_ok):<8} | {note}")

    print("\n==================================================")
    print(f"BASELINE NON-COMPLIANT TICKS ({len(base_failures)}): {base_failures}")
    print(f"AGENT BASELINE NON-COMPLIANT TICKS ({len(agent_failures)}): {agent_failures}")
    print(f"TICKS WHERE COMPLIANCE STATS DIFFER ({len(diff_ticks)}): {diff_ticks}")
    print("==================================================")

if __name__ == "__main__":
    compare_ticks()
