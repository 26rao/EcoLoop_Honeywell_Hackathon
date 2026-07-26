import json
import urllib.request

prompt = """You are the EcoLoop Autonomous Building Management Agent.
Analyze the current building state and recommend updated heating and cooling setpoints.

CURRENT BUILDING STATE:
{
  "sim_timestamp": "2026-07-25T14:33:55Z",
  "zone_temps_c": {"MainZone": 25.5},
  "pmv": 0.8,
  "occupancy_fraction": 1.0,
  "heating_energy_rate_w": 0.0,
  "cooling_energy_rate_w": 4500.0,
  "outdoor_temp_c": 32.0,
  "lookahead_outdoor_temp_c": [33.0, 31.5, 29.0, 26.0],
  "thermal_history": [],
  "carbon_intensity_gco2_kwh": 320.0,
  "cumulative_energy_kwh": 45.2,
  "current_heating_setpoint_c": 21.0,
  "current_cooling_setpoint_c": 24.0
}

INSTRUCTIONS:
Respond ONLY with a valid JSON object matching this schema:
{
  "heating_setpoint_c": float,
  "cooling_setpoint_c": float,
  "rationale": "non-empty explanation string"
}
"""

payload = {
    "model": "mistral:latest",
    "messages": [{"role": "user", "content": prompt}],
    "stream": False,
    "format": "json"
}

url = "http://localhost:11434/api/chat"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print("Sending request to Ollama...")
with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print("RAW OLLAMA RESPONSE:")
    print(json.dumps(res, indent=2))
