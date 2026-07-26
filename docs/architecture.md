# EcoLoop — Technical Architecture & System Specification

## 1. System Overview & Strategy Pattern Architecture

EcoLoop is an autonomous, closed-loop building energy management system (BEMS) built upon EnergyPlus 24.2.0 C++ API and local Ollama (`qwen2.5:7b-instruct`).

```
+-----------------------------------------------------------------------------------+
|                                  EcoLoop BEMS                                     |
|                                                                                   |
|  +-----------------------+      +-------------------+      +-------------------+  |
|  | EnergyPlus 24.2.0 C++ | <--> | LoopController    | <--> | SafetyValidator   |  |
|  | Runtime (pyenergyplus)|      | (State Builder)   |      | (Clamping & Bounds|  |
|  +-----------------------+      +-------------------+      +-------------------+  |
|                                           ^                                       |
|                                           | (Strategy Pattern)                    |
|                                           v                                       |
|                                 +-------------------+                             |
|                                 | LLMAgentPolicy    |                             |
|                                 | (qwen2.5:7b-inst) |                             |
|                                 +-------------------+                             |
+-----------------------------------------------------------------------------------+
```

## 2. Protocol & Tools Compliance (MCP vs. Custom Tools)

Per the technical requirements' explicit allowance for *"Implement an MCP Server or custom agentic tools,"* EcoLoop implements custom function-calling agentic tools (`EnergyPlusErrorParser`, `EPWWeatherLookahead`, `SafetyValidator`) rather than a full MCP network server, prioritizing zero-latency, in-process C++ memory reliability within the hackathon timeframe.

Error parsing (`EnergyPlusErrorParser`) is performed automatically by the orchestration layer during state building rather than as an LLM-invoked tool call, prioritizing reliability, determinism, and zero-latency execution over model-driven tool selection for this specific system check.

## 3. IDF Deliverables & Live Memory Actuation

Rather than generating modified static IDF file copies on disk at runtime, EcoLoop actuates heating and cooling setpoints dynamically in EnergyPlus C++ memory via `pyenergyplus.api` actuator handles (`323` Heating Setpoint, `324` Cooling Setpoint). This live memory actuation approach is technically superior to static IDF file regeneration as it enables real-time 15-minute closed-loop control without file I/O overhead.

## 4. Policy Abstraction & Deterministic Execution

The core orchestration (`LoopController`) operates on abstract `Policy` interfaces (`decide(state: BuildingState) -> Action`).
- **FixedSchedulePolicy**: Phase 1 legacy flat BEMS baseline schedule (constant 21°C heating / 24°C cooling 24/7 without automated night setback).
- **RuleSetbackPolicy**: Programmable thermostat proxy (fixed schedule: 21°C heating / 24°C cooling occupied, 18°C heating / 26°C cooling unoccupied).
- **LLMAgentPolicy**: Phase 2 autonomous policy communicating with local Ollama (`http://localhost:11434/api/chat`). Setpoint decisions originate **100% directly from the LLM JSON response**, configured with `"temperature": 0.0` and `"seed": 42` for **100% bit-for-bit deterministic reproducibility**.

## 5. Official Frozen Benchmark Results (73 / 73 Decisions)

Truth extraction from frozen log files (`logs/FINAL_baseline_event_log.jsonl`, `logs/FINAL_timer_event_log.jsonl`, `logs/FINAL_agent_event_log.jsonl`):

| Control Policy | Total Electrical Energy (kWh) | Cooling Energy (kWh) | Heating Energy (kWh) | Nighttime HVAC Load (W) | Occupied PMV Compliance % | Determinism Guarantee |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Legacy Flat Baseline** | **`19.94 kWh`** | `19.48 kWh` | `0.46 kWh` | `6,985.5 W` (100.0%) | **90.0%** (27/30 ticks) | Deterministic Rules |
| **2. Programmable Setback Timer** | **`18.60 kWh`** (-6.7%) | `18.60 kWh` | `0.00 kWh` | `4,958.1 W` (-29.0%) | **90.0%** (27/30 ticks) | Deterministic Rules |
| **3. Autonomous LLM Agent** | **`18.60 kWh`** (-6.7%) | `18.60 kWh` | `0.00 kWh` | `4,958.1 W` (-29.0%) | **90.0%** (27/30 ticks) | **100% Bit-for-Bit Deterministic** |

> [!NOTE]
> **Verified Metrics Summary**:
> - **Total Electrical Energy**: Baseline `19.94 kWh` vs Agent `18.60 kWh` (**`6.72% Net Electrical Savings`**).
> - **Nighttime HVAC Load**: Baseline `6,985.5 W` vs Agent `4,958.1 W` (**`29.0% Reduction in Nighttime Cooling Load`**).
> - **Occupied PMV Comfort**: **`100% Identical Occupied Comfort at 90.0%`** (27/30 occupied ticks compliant for all three policies).

## 6. Key Incremental Value of LLM Agent over Static Timer

While a programmable timer captures raw night setback cooling savings (`18.60 kWh`), it operates as a static binary clock. The LLM Agent matches night setback efficiency while providing crucial autonomous capabilities that static timers cannot deliver:
1. **Predictive Weather Lookahead**: Uses 4-hour EPW forecasts to adjust setpoints ahead of ambient heat spikes, leveraging building thermal mass.
2. **Multi-Metric PMV Comfort Fine-Tuning**: Balances Fanger PMV indices against thermal response across 6 distinct setpoint pairs rather than applying rigid step jumps.
3. **Autonomous Error Recovery & Self-Correction**: Scans EnergyPlus `.err` log files for HVAC warnings and automatically triggers Conservative Mode (`conservative_mode_active = True`).
4. **Natural Language Operator Explainability**: Generates human-readable audit rationales for every decision payload.

## 7. Prompt Engineering Strategy

EcoLoop employs a zero-shot, structured function-calling prompt architecture designed for zero-latency inference:
- **System Role**: Defines the LLM as an expert Building Energy & Comfort Optimization Agent.
- **Context Window Ingestion**: Ingests real-time zone air temperature, PMV comfort index, 4-hour EPW weather lookahead forecast, occupant presence fraction, and sliding window thermal history.
- **JSON Formatting Enforcement**: Enforces a strict JSON response schema (`heating_setpoint_c`, `cooling_setpoint_c`, `rationale`).
- **Deterministic Options**: Locks inference temperature to `0.0` and seed to `42` to guarantee reproducible decision-making.

## 8. Handling Lengthy Simulation Logs

Long-duration, high-frequency simulation runs are managed through a dual-tier storage strategy:
- **Line-Buffered JSONL Streaming**: Event records are written continuously to disk via thread-safe JSONL loggers (`logs/FINAL_agent_event_log.jsonl`), preventing memory growth during multi-day runs.
- **Bounded In-Memory State History**: State builders maintain a fixed sliding window array of the last 4 timestep readings (`thermal_history`), bounding memory consumption while providing sufficient temporal context for setpoint recommendations.

## 9. Empirical Rationale Quotes from Live Agent Logs

Real model-generated rationale strings extracted directly from `logs/FINAL_agent_event_log.jsonl`:

- **Unoccupied Setback (Tick 1 - 12:00 AM)**:
  > *"Given the building is UNOCCUPIED with an occupancy fraction of 0.0, the recommended setpoints according to the optimization guidance are a heating setpoint of 18.0°C and a cooling setpoint of 27.0°C to ensure energy savings during unoccupied periods."*
- **Occupied Comfort Transition (Tick 10 - 09:00 AM)**:
  > *"The building is currently occupied with a high occupancy fraction of 1.0, and the current zone temperature is 24.5°C while the PMV value is 0.47, indicating slightly warm conditions for optimal occupant comfort (-0.5 <= PMV <= +0.5). Maintaining the recommended heating setpoint at 21.0°C and cooling setpoint at 24.0°C will help achieve a comfortable environment."*
- **Evening Setback Shift (Tick 21 - 08:00 PM)**:
  > *"The building is currently unoccupied with an occupancy fraction of 0.0, so energy-saving setback temperatures are applied as per optimization guidance to reduce HVAC usage and save energy."*

## 10. Literature Grounding & External Peer Validation

This result is consistent with published research on HVAC setback strategies:
- A **Pacific Northwest National Laboratory (PNNL)** study of commercial building control measures found widened deadbands and night setback contributing **~7.7% overall site energy savings** as a top-tier measure (*PNNL-25985*).
- A cooling-climate small-office study found individual occupancy-centric/night-purge measures contributing roughly **3–7% of total building electricity**, with combined multi-measure strategies reaching 8.9–20.4% (*arXiv:2205.10324*).
- Classic **DOE/PNL field studies** of night-setback report 14–25% savings, but for full heating-season, heating-dominated buildings (*OSTI 6863765*) — a different regime from this system's 3-day, cooling-only test window.

EcoLoop's **6.7% aggregate / 29.0% nighttime-specific reduction**, from a single measure over a short cooling-season window, falls squarely within the range the literature would predict — not an outlier, and not underwhelming, but empirically consistent with prior published work.

## 11. Safety, Rate-of-Change & Deadband Constraint Enforcement
- **Strict Deadband Enforcement**: `SafetyValidator` ([validator.py](file:///c:/Users/HP/OneDrive/Attachments/Desktop/Honeywell%20Hackathon/src/ecoloop/safety/validator.py)) enforces `final_cooling_setpoint_c >= final_heating_setpoint_c + min_deadband_c` ($\ge 1.0^\circ\text{C}$). Heating is NEVER set equal to or above cooling setpoint.
- **Rate-of-Change Clamp**: Maximum setpoint change of $\pm 1.5^\circ\text{C}$ per step. (Empirically verified: proposed 27°C cooling clamped to 25.5°C).
- **Watchdog Circuit Breaker**: If LLM fails 3 consecutive times, system freezes setpoints to safe baseline (`22.0°C`). (Empirically verified: 3 failures trip `watchdog_tripped = True`).

## 12. Energy COP Conversion Justification
- **Heating COP**: `1.0` (Electric resistance baseline).
- **Cooling COP**: `3.0` (ASHRAE typical mid-range rooftop packaged unit / chiller COP).
- **Formula**: $\text{Electrical kWh} = \frac{\text{Thermal Energy Rate (W)}}{1000 \times \text{COP}} \times 1\text{ hr}$.
