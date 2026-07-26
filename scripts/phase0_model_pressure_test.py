import sys
import os
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecoloop.state.schema import BuildingState, HistoryPoint
from ecoloop.tools.schemas import TOOLS

def generate_10_synthetic_states() -> list[BuildingState]:
    now = datetime.now(timezone.utc)
    states = []

    # 1. Hot afternoon, high occupancy
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 25.5}, pmv=0.8, occupancy_fraction=1.0,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=4500.0, outdoor_temp_c=32.0,
        lookahead_outdoor_temp_c=[33.0, 31.5, 29.0, 26.0], thermal_history=[],
        carbon_intensity_gco2_kwh=320.0, cumulative_energy_kwh=45.2,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 2. Cool morning, heating needed
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 19.2}, pmv=-1.2, occupancy_fraction=0.5,
        heating_energy_rate_w=3200.0, cooling_energy_rate_w=0.0, outdoor_temp_c=10.0,
        lookahead_outdoor_temp_c=[12.0, 15.0, 18.0, 20.0], thermal_history=[],
        carbon_intensity_gco2_kwh=180.0, cumulative_energy_kwh=12.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 3. Evening unoccupied, high carbon intensity
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 22.5}, pmv=0.1, occupancy_fraction=0.0,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=500.0, outdoor_temp_c=24.0,
        lookahead_outdoor_temp_c=[22.0, 20.0, 19.0, 18.0], thermal_history=[],
        carbon_intensity_gco2_kwh=450.0, cumulative_energy_kwh=62.8,
        current_heating_setpoint_c=18.0, current_cooling_setpoint_c=27.0
    ))

    # 4. Optimal thermal comfort
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 22.1}, pmv=0.0, occupancy_fraction=0.8,
        heating_energy_rate_w=100.0, cooling_energy_rate_w=200.0, outdoor_temp_c=22.0,
        lookahead_outdoor_temp_c=[22.5, 23.0, 22.0, 21.0], thermal_history=[],
        carbon_intensity_gco2_kwh=210.0, cumulative_energy_kwh=30.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 5. Rapid temperature drop expected
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 23.0}, pmv=0.3, occupancy_fraction=1.0,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=1200.0, outdoor_temp_c=26.0,
        lookahead_outdoor_temp_c=[20.0, 15.0, 11.0, 8.0], thermal_history=[],
        carbon_intensity_gco2_kwh=280.0, cumulative_energy_kwh=88.5,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 6. EDGE CASE: Near lower comfort boundary (21.1°C zone temp, PMV -0.7)
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 21.1}, pmv=-0.7, occupancy_fraction=1.0,
        heating_energy_rate_w=800.0, cooling_energy_rate_w=0.0, outdoor_temp_c=14.0,
        lookahead_outdoor_temp_c=[13.0, 12.0, 11.0, 10.0], thermal_history=[],
        carbon_intensity_gco2_kwh=290.0, cumulative_energy_kwh=102.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 7. EDGE CASE: Near upper comfort boundary (25.9°C zone temp, PMV +0.9)
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 25.9}, pmv=0.9, occupancy_fraction=0.9,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=3800.0, outdoor_temp_c=34.0,
        lookahead_outdoor_temp_c=[35.0, 36.0, 35.0, 33.0], thermal_history=[],
        carbon_intensity_gco2_kwh=380.0, cumulative_energy_kwh=115.4,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 8. EDGE CASE: Partial transient occupancy (0.15 fraction)
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 23.5}, pmv=0.2, occupancy_fraction=0.15,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=300.0, outdoor_temp_c=25.0,
        lookahead_outdoor_temp_c=[24.0, 23.0, 22.0, 21.0], thermal_history=[],
        carbon_intensity_gco2_kwh=190.0, cumulative_energy_kwh=50.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 9. EDGE CASE: Extreme outdoor heatwave (39.0°C ambient)
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 26.5}, pmv=1.3, occupancy_fraction=1.0,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=6000.0, outdoor_temp_c=39.0,
        lookahead_outdoor_temp_c=[40.0, 41.0, 39.0, 36.0], thermal_history=[],
        carbon_intensity_gco2_kwh=510.0, cumulative_energy_kwh=140.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    # 10. EDGE CASE: Zero grid carbon (100% renewable hour)
    states.append(BuildingState(
        sim_timestamp=now, zone_temps_c={"MainZone": 22.8}, pmv=0.0, occupancy_fraction=0.7,
        heating_energy_rate_w=0.0, cooling_energy_rate_w=1000.0, outdoor_temp_c=27.0,
        lookahead_outdoor_temp_c=[28.0, 27.0, 25.0, 24.0], thermal_history=[],
        carbon_intensity_gco2_kwh=12.0, cumulative_energy_kwh=75.0,
        current_heating_setpoint_c=21.0, current_cooling_setpoint_c=24.0
    ))

    return states

def build_prompt(state: BuildingState) -> str:
    return f"""You are the EcoLoop Autonomous Building Management Agent.
Analyze the current building state and recommend updated heating and cooling setpoints.

AVAILABLE TOOLS:
{json.dumps(TOOLS, indent=2)}

CURRENT BUILDING STATE:
{state.model_dump_json(indent=2)}

INSTRUCTIONS:
1. Choose heating and cooling setpoints within comfort range (21.0°C - 26.0°C).
2. Respond ONLY with a valid JSON object matching this schema:
{{
  "heating_setpoint_c": float,
  "cooling_setpoint_c": float,
  "rationale": "non-empty explanation string"
}}
"""

def query_live_ollama(prompt: str, model_name: str = "qwen2.5:7b-instruct", keep_alive: str = "30m") -> tuple[str, float]:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "keep_alive": keep_alive
    }

    start_time = time.time()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        latency = time.time() - start_time
        content = res_data.get("message", {}).get("content", "")
        return content, latency

def warmup_model(model_name: str = "qwen2.5:7b-instruct"):
    print(f"Executing warm-up call for model '{model_name}' (keep_alive='30m')...")
    start = time.time()
    try:
        _, latency = query_live_ollama("Respond with JSON: {\"status\": \"ok\"}", model_name=model_name, keep_alive="30m")
        print(f"Warm-up complete in {round(latency, 2)}s. Model loaded in memory.")
    except Exception as e:
        print(f"Warm-up call notice: {e}")

def run_phase0_10_payload_audit(target_model: str = "qwen2.5:7b-instruct"):
    states = generate_10_synthetic_states()
    passed = 0
    total = len(states)

    print("==================================================")
    print(f"EcoLoop Phase 0 Audit — Live 10-Payload Pressure Test")
    print(f"Target Model: {target_model} (Ollama Live Endpoint)")
    print("==================================================")

    warmup_model(target_model)

    results = []

    for idx, state in enumerate(states, 1):
        prompt = build_prompt(state)
        try:
            raw_response, latency = query_live_ollama(prompt, model_name=target_model, keep_alive="30m")
            parsed = json.loads(raw_response)

            heating = parsed.get("heating_setpoint_c")
            cooling = parsed.get("cooling_setpoint_c")
            rationale = str(parsed.get("rationale", "")).strip()

            valid = (
                isinstance(heating, (int, float)) and
                isinstance(cooling, (int, float)) and
                len(rationale) > 5 and
                18.0 <= heating <= 28.0 and
                18.0 <= cooling <= 28.0
            )

            if valid:
                passed += 1
                status_str = "PASSED"
            else:
                status_str = "FAILED"

            print(f"[{idx}/{total}] {status_str} ({round(latency, 2)}s)")
            print(f"    Proposed: Heating={heating}°C, Cooling={cooling}°C")
            print(f"    Rationale: {rationale[:80]}...")

            results.append({
                "index": idx,
                "status": status_str,
                "latency_s": round(latency, 2),
                "heating_c": heating,
                "cooling_c": cooling,
                "rationale": rationale,
                "raw_response": raw_response
            })

        except Exception as e:
            print(f"[{idx}/{total}] ERROR -> {e}")

    pass_rate = (passed / total) * 100.0
    print("\n--------------------------------------------------")
    print(f"Phase 0 Audit Results ({target_model}): {passed}/{total} passed ({pass_rate:.1f}% compliance)")
    print("--------------------------------------------------")

    os.makedirs("logs", exist_ok=True)
    with open("logs/phase0_audit_results.json", "w", encoding="utf-8") as f:
        json.dump({"target_model": target_model, "pass_rate": pass_rate, "total": total, "passed": passed, "results": results}, f, indent=2)

if __name__ == "__main__":
    # Check if qwen2.5:7b-instruct or mistral:latest is available
    import subprocess
    output = subprocess.getoutput("ollama list")
    model = "qwen2.5:7b-instruct" if "qwen2.5:7b-instruct" in output else "mistral:latest"
    run_phase0_10_payload_audit(model)
