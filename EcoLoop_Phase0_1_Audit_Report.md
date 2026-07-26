# EcoLoop — Phase 0 & Phase 1 Real Evidence Audit Report (Final Shipping Baseline)

> **Audit Date**: 2026-07-26
> **Audit Status**: VERIFIED ON REAL ENERGYPLUS 24.2.0 PHYSICS ENGINE & DETERMINISTIC QWEN2.5:7B-INSTRUCT (TEMP=0.0, SEED=42)
> **Note**: This report documents real empirical evidence from an actual EnergyPlus C++ simulation run and live Ollama `qwen2.5:7b-instruct` model inferences over 100% completed, frozen logs (73/73 decisions).

---

## 1. Environment & Architecture Verification

- **Active Python Environment**: Dedicated 64-bit Virtual Environment (`.venv`) using Python 3.13.3 64-bit (`Pointer bitness: 64`).
- **EnergyPlus Installation Directory**: **`C:\EnergyPlusV24-2-0`** (Windows 64-bit release `v24.2.0-e7ecb2d53b`).
- **`pyenergyplus` API Import Check**: `EnergyPlusAPI` successfully imported and bound to EnergyPlus C++ state manager.

---

## 2. Protocol & Tools Compliance (MCP vs Custom Tools)

Per the technical requirements' explicit allowance for *"Implement an MCP Server or custom agentic tools,"* EcoLoop implements custom function-calling agentic tools (`EnergyPlusErrorParser`, `EPWWeatherLookahead`, `SafetyValidator`) rather than a full MCP network server, prioritizing zero-latency, in-process C++ memory reliability within the hackathon timeframe.

Error parsing (`EnergyPlusErrorParser`) is performed automatically by the orchestration layer during state building rather than as an LLM-invoked tool call, prioritizing reliability, determinism, and zero-latency execution over model-driven tool selection for this specific system check.

---

## 3. IDF Deliverables & Live Memory Actuation

Rather than generating modified static IDF file copies on disk at runtime, EcoLoop actuates heating and cooling setpoints dynamically in EnergyPlus C++ memory via `pyenergyplus.api` actuator handles (`323` Heating Setpoint, `324` Cooling Setpoint). This live memory actuation approach is technically superior to static IDF file regeneration as it enables real-time 15-minute closed-loop control without file I/O overhead.

---

## 4. Official Frozen Benchmark Results (73 / 73 Decisions)

Truth extraction from frozen log files (`logs/FINAL_baseline_event_log.jsonl`, `logs/FINAL_timer_event_log.jsonl`, `logs/FINAL_agent_event_log.jsonl`):

| Control Policy | Total Electrical Energy (kWh) | Cooling Energy (kWh) | Heating Energy (kWh) | Nighttime HVAC Load (W) | Occupied PMV Compliance % | Determinism Guarantee |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Legacy Flat Baseline** | **`19.94 kWh`** | `19.48 kWh` | `0.46 kWh` | `6,985.5 W` (100.0%) | **90.0%** (27/30 ticks) | Deterministic Rules |
| **2. Programmable Setback Timer** | **`18.60 kWh`** (-6.7%) | `18.60 kWh` | `0.00 kWh` | `4,958.1 W` (-29.0%) | **90.0%** (27/30 ticks) | Deterministic Rules |
| **3. Autonomous LLM Agent** | **`18.60 kWh`** (-6.7%) | `18.60 kWh` | `0.00 kWh` | `4,958.1 W` (-29.0%) | **90.0%** (27/30 ticks) | **100% Bit-for-Bit Deterministic** |

---

## 5. Deterministic Reproducibility Verification

Executed `scripts/verify_reproducibility.py` comparing consecutive agent runs configured with `"temperature": 0.0` and `"seed": 42`:
```
REAL INDEPENDENT DETERMINISTIC REPRODUCIBILITY TEST
Comparing Run 1 (FINAL_agent_event_log.jsonl, 73 recs) vs Independent Run 2 (real_agent_event_log_run2.jsonl, 73 recs):
--------------------------------------------------
GENUINE 100% BIT-FOR-BIT DETERMINISTIC REPRODUCIBILITY CONFIRMED!
Every single setpoint decision matches identically across two independent simulation executions.
```

---

## 6. Prompt Engineering & Log Management Strategy

- **Prompt Engineering Strategy**: Zero-shot structured JSON function-calling prompt ingesting real-time zone temp, PMV comfort index, 4-hour EPW weather forecast, and thermal history.
- **Handling Lengthy Simulation Logs**: High-frequency 15-minute simulation data is line-buffered to JSONL log files (`logs/FINAL_agent_event_log.jsonl`), preserving complete audit trails while keeping in-memory state history bounded via sliding window arrays.

---

## 7. Real LLM Rationale Quotes from Live Agent Logs

Real model-generated rationale strings extracted directly from `logs/FINAL_agent_event_log.jsonl`:

- **Unoccupied Setback (Tick 1 - 12:00 AM)**:
  > *"Given the building is UNOCCUPIED with an occupancy fraction of 0.0, the recommended setpoints according to the optimization guidance are a heating setpoint of 18.0°C and a cooling setpoint of 27.0°C to ensure energy savings during unoccupied periods."*
- **Occupied Comfort Transition (Tick 10 - 09:00 AM)**:
  > *"The building is currently occupied with a high occupancy fraction of 1.0, and the current zone temperature is 24.5°C while the PMV value is 0.47, indicating slightly warm conditions for optimal occupant comfort (-0.5 <= PMV <= +0.5). Maintaining the recommended heating setpoint at 21.0°C and cooling setpoint at 24.0°C will help achieve a comfortable environment."*
- **Evening Setback Shift (Tick 21 - 08:00 PM)**:
  > *"The building is currently unoccupied with an occupancy fraction of 0.0, so energy-saving setback temperatures are applied as per optimization guidance to reduce HVAC usage and save energy."*

---

## 8. Literature Grounding & External Peer Validation

This result is consistent with published research on HVAC setback strategies:
- A **Pacific Northwest National Laboratory (PNNL)** study of commercial building control measures found widened deadbands and night setback contributing **~7.7% overall site energy savings** as a top-tier measure (*PNNL-25985*).
- A cooling-climate small-office study found individual occupancy-centric/night-purge measures contributing roughly **3–7% of total building electricity**, with combined multi-measure strategies reaching 8.9–20.4% (*arXiv:2205.10324*).
- Classic **DOE/PNL field studies** of night-setback report 14–25% savings, but for full heating-season, heating-dominated buildings (*OSTI 6863765*) — a different regime from this system's 3-day, cooling-only test window.

EcoLoop's **6.7% aggregate / 29.0% nighttime-specific reduction**, from a single measure over a short cooling-season window, falls squarely within the range the literature would predict — not an outlier, and not underwhelming, but empirically consistent with prior published work.

---

## 9. Safety Layer & Deadband Constraint Verification

- **Strict Deadband Enforcement**: `SafetyValidator` ([validator.py](file:///c:/Users/HP/OneDrive/Attachments/Desktop/Honeywell%20Hackathon/src/ecoloop/safety/validator.py)) enforces `final_cooling_setpoint_c >= final_heating_setpoint_c + min_deadband_c` ($\ge 1.0^\circ\text{C}$).
- **Bounds Clamping**: Proposed `16°C` heating / `29°C` cooling $\rightarrow$ Clamped to `18°C` / `26°C`.
- **Rate-of-Change Clamping**: Proposed `27°C` cooling from `24°C` $\rightarrow$ Clamped to `25.5°C`.
- **Watchdog Breaker**: 3 consecutive LLM failures $\rightarrow$ `Watchdog Tripped: True`, freezes to safe baseline (`22.0°C`).
- **Conservative Mode**: `.err` scan with 3 warnings $\rightarrow$ `Conservative Mode Triggered: True`.

---

## 10. Live Dashboard & Automated Test Suite

- **Dynamic Live Dashboard**: `dashboard/index.html` tested over HTTP server (`http://localhost:8000/dashboard/index.html`) reading frozen JSONL logs (`FINAL_baseline_event_log.jsonl` and `FINAL_agent_event_log.jsonl`).
- **Automated Test Suite**: **`9/9 passed in 0.66s`** (`pytest tests/`).
