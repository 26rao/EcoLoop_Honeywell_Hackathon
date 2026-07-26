import json
from pathlib import Path

log_path = Path("logs/real_baseline_event_log.jsonl")
if not log_path.exists():
    log_path = Path("logs/baseline_event_log.jsonl")

if not log_path.exists():
    print("Log file not found.")
else:
    pmv_values = []
    mock_flags = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                pmv = record.get("state", {}).get("pmv")
                mock_mode = record.get("mock_mode", False)
                mock_flags.append(mock_mode)
                if pmv is not None:
                    pmv_values.append(pmv)

    if pmv_values:
        min_pmv = min(pmv_values)
        max_pmv = max(pmv_values)
        mean_pmv = sum(pmv_values) / len(pmv_values)
        print("==================================================")
        print(f"REAL ENERGYPLUS SIMULATION PMV METRICS ({len(pmv_values)} records):")
        print(f"- Log File: {log_path}")
        print(f"- Mock Mode Active: {any(mock_flags)}")
        print(f"- Min PMV:  {min_pmv:.2f}")
        print(f"- Max PMV:  {max_pmv:.2f}")
        print(f"- Mean PMV: {mean_pmv:.2f}")
        print("==================================================")
