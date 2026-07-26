import json
import time
import urllib.request
from typing import Tuple, Dict, Any, Optional
from ecoloop.state.schema import BuildingState, Action
from ecoloop.policy.fixed_schedule import FixedSchedulePolicy

class LLMAgentPolicy:
    """Phase 2 Autonomous LLM Policy using Ollama qwen2.5:7b-instruct structured JSON response."""

    name: str = "llm_agent"

    def __init__(self, config: dict, ollama_url: str = "http://localhost:11434/api/chat", model_name: str = "qwen2.5:7b-instruct"):
        self.config = config
        self.ollama_url = config.get("ollama_url", ollama_url)
        self.model_name = config.get("ollama_model", model_name)
        self.timeout_s = float(config.get("llm_timeout_s", 35.0))
        self.max_retries = int(config.get("max_retries", 2))

        self.consecutive_failures = 0
        self.watchdog_tripped = False
        self.fallback_policy = FixedSchedulePolicy()

    def warmup(self):
        """Warm up Ollama model into GPU memory."""
        print(f"[{self.name}] Executing warm-up call for model '{self.model_name}' (keep_alive='30m')...")
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}],
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": 0.0,
                "seed": 42
            }
        }
        start_t = time.time()
        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency = time.time() - start_t
                print(f"[{self.name}] Warm-up completed in {latency:.2f}s. Model loaded into memory.")
        except Exception as e:
            print(f"[{self.name}] Warm-up call warning: {e}")

    def _build_prompt(self, state: BuildingState) -> str:
        occ_str = "OCCUPIED" if state.occupancy_fraction > 0 else "UNOCCUPIED"
        guidance = "Prioritize occupant comfort (PMV near 0.0)." if state.occupancy_fraction > 0 else "Apply energy-saving setback temperatures."

        mode_note = ""
        if hasattr(state, "conservative_mode_active") and getattr(state, "conservative_mode_active"):
            mode_note = "\nCONSERVATIVE MODE ACTIVE: HVAC warnings detected. Tighten deadbands and avoid aggressive setpoints."

        return f"""You are the EcoLoop Autonomous Building Energy & Comfort Optimization Agent.
Analyze the building state and recommend optimal heating and cooling setpoints.

BUILDING STATUS: {occ_str} (Occupancy Fraction: {state.occupancy_fraction})
OPTIMIZATION GUIDANCE: {guidance}{mode_note}

CURRENT BUILDING STATE:
{state.model_dump_json(indent=2)}

INSTRUCTIONS:
1. When OCCUPIED (occupancy > 0): Heating setpoint 21.0°C, Cooling setpoint 24.0°C.
2. When UNOCCUPIED (occupancy = 0): Heating setpoint 18.0°C, Cooling setpoint 27.0°C.
3. Respond ONLY with a valid JSON object matching this schema:
{{
  "heating_setpoint_c": float,
  "cooling_setpoint_c": float,
  "rationale": "non-empty explanation string"
}}
"""

    def _call_ollama(self, prompt: str) -> Tuple[dict, float]:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": 0.0,
                "seed": 42
            }
        }
        start_t = time.time()
        req = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latency = time.time() - start_t
            content = data.get("message", {}).get("content", "")
            parsed = json.loads(content)
            return parsed, latency

    def decide(self, state: BuildingState) -> Action:
        start_t = time.time()

        if self.watchdog_tripped:
            fb_action = self.fallback_policy.decide(state)
            fb_action.rationale = f"[WATCHDOG CIRCUIT BREAKER ACTIVE] {fb_action.rationale}"
            fb_action.latency_s = round(time.time() - start_t, 3)
            return fb_action

        prompt = self._build_prompt(state)

        for attempt in range(1 + self.max_retries):
            try:
                parsed, latency = self._call_ollama(prompt)
                heating = float(parsed["heating_setpoint_c"])
                cooling = float(parsed["cooling_setpoint_c"])
                rationale = str(parsed.get("rationale", "LLM setpoint optimization")).strip()

                if not (18.0 <= heating <= 26.0 and 18.0 <= cooling <= 28.0):
                    raise ValueError(f"LLM setpoints out of bounds: heating={heating}, cooling={cooling}")

                self.consecutive_failures = 0
                return Action(
                    heating_setpoint_c=heating,
                    cooling_setpoint_c=cooling,
                    rationale=rationale,
                    latency_s=round(latency, 3)
                )
            except Exception as e:
                print(f"[{self.name}] Attempt {attempt + 1} failed: {e}")

        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.watchdog_tripped = True
            print(f"[{self.name}] WATCHDOG TRIP: {self.consecutive_failures} consecutive LLM failures. Freezing to FixedSchedulePolicy.")

        fb_action = self.fallback_policy.decide(state)
        fb_action.rationale = f"[LLM FALLBACK (attempt failed)] {fb_action.rationale}"
        fb_action.latency_s = round(time.time() - start_t, 3)
        return fb_action
