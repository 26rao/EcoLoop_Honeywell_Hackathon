import json
from pathlib import Path
from typing import Dict, Any

class PerformanceMetricsCalculator:
    """Calculates COP-adjusted electrical energy consumption and PMV thermal comfort metrics."""

    COOLING_COP = 3.0
    HEATING_COP = 1.0

    def calculate_metrics(self, event_log_path: str) -> Dict[str, Any]:
        path = Path(event_log_path)
        if not path.exists():
            return {}

        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        if not records:
            return {}

        total_records = len(records)
        total_heating_wh = sum(r["state"].get("heating_energy_rate_w", 0.0) for r in records)
        total_cooling_wh = sum(r["state"].get("cooling_energy_rate_w", 0.0) for r in records)

        heating_kwh = (total_heating_wh / 1000.0) / self.HEATING_COP
        cooling_kwh = (total_cooling_wh / 1000.0) / self.COOLING_COP
        total_kwh = heating_kwh + cooling_kwh

        all_pmvs = [r["state"]["pmv"] for r in records]
        occ_pmvs = [r["state"]["pmv"] for r in records if r["state"].get("occupancy_fraction", 1.0) > 0]

        all_compliant = sum(1 for p in all_pmvs if -0.5 <= p <= 0.5)
        occ_compliant = sum(1 for p in occ_pmvs if -0.5 <= p <= 0.5)

        all_comfort_pct = (all_compliant / len(all_pmvs)) * 100.0 if all_pmvs else 0.0
        occ_comfort_pct = (occ_compliant / len(occ_pmvs)) * 100.0 if occ_pmvs else 0.0

        latencies = [r.get("wall_clock_latency_s", 0.0) for r in records if r.get("wall_clock_latency_s")]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total_records": total_records,
            "occupied_records": len(occ_pmvs),
            "heating_kwh": round(heating_kwh, 2),
            "cooling_kwh": round(cooling_kwh, 2),
            "total_kwh": round(total_kwh, 2),
            "pmv_min": round(min(all_pmvs), 2),
            "pmv_max": round(max(all_pmvs), 2),
            "pmv_mean": round(sum(all_pmvs) / len(all_pmvs), 2),
            "all_hours_comfort_pct": round(all_comfort_pct, 1),
            "occupied_comfort_pct": round(occ_comfort_pct, 1),
            "avg_latency_s": round(avg_latency, 2)
        }

if __name__ == "__main__":
    calc = PerformanceMetricsCalculator()
    b_metrics = calc.calculate_metrics("logs/real_baseline_event_log.jsonl")
    a_metrics = calc.calculate_metrics("logs/real_agent_event_log.jsonl")

    savings_pct = 0.0
    if b_metrics.get("total_kwh") and a_metrics.get("total_kwh"):
        savings_pct = ((b_metrics["total_kwh"] - a_metrics["total_kwh"]) / b_metrics["total_kwh"]) * 100.0

    print(json.dumps({
        "baseline": b_metrics,
        "agent": a_metrics,
        "kwh_savings_pct": round(savings_pct, 1)
    }, indent=2))
