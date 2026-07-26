# EcoLoop — Autonomous Closed-Loop Building Management System
## Master Build Brief for Antigravity Agent

> **How to use this file:** Save this as `BUILD_BRIEF.md` in the repo root. Give the agent a short task: *"Read BUILD_BRIEF.md in full before writing any code. Produce an implementation plan artifact for Phase 0 and Phase 1 only, and wait for my confirmation before proceeding to Phase 2."* Do not paste this as a single chat message — let the agent read it as a file so it stays in context across the whole session.
>
> **Model note:** The model Antigravity uses to run *you*, the coding agent (Gemini 3 Pro / Claude / GPT‑OSS), is unrelated to the **local open-source LLM** this project calls at runtime as the building's decision-making brain (Qwen2.5-Instruct, see §8). Do not conflate the two. You are building software that calls a *separate*, locally-hosted model — you are not simulating that model's behavior yourself.

---

## 1. Mission

Build a working, autonomous, closed-loop Building Management System for a hackathon (Honeywell, Round 2 — "Eco-Loop Building Agents"). EnergyPlus is the physics engine (a real building's digital twin); a local open-source LLM is the decision-making brain. The system must read live simulation state, reason about energy/comfort/carbon, and write new setpoints back into the running simulation — continuously, without restarting, without crashing, and with numbers that hold up under a technically sharp judge's questioning.

This is a **weekend build**. Every architectural choice below exists to reduce risk, not to look impressive. Reliability and honesty outrank sophistication at every decision point.

---

## 2. Evaluation Criteria (govern every tradeoff you make)

| Criterion | Weight | What it actually rewards |
|---|---|---|
| System Integration | 30% | Loop survives the full simulated horizon with zero crashes |
| Energy Efficiency Realized | 25% | Real, defensible % kWh reduction vs. baseline |
| Thermal Comfort & Constraints | 20% | Comfort never silently sacrificed for savings |
| Agentic Autonomy & Code Elegance | 15% | Real tool-calling, self-correction, clean architecture |
| Presentation & Documentation | 10% | Clear arch doc, reproducible numbers, tight video |

**Rule of thumb:** if a feature doesn't clearly serve one of these five rows, it is out of scope this weekend. See §13 for the exact cut list.

---

## 3. Non-Negotiable Requirements

These come directly from the problem statement — do not hedge, stub, or defer any of them:

1. **PMV must be streamed and used**, computed via EnergyPlus's native Fanger model (People object with clothing insulation, metabolic rate, air velocity properly configured) — not a temperature-deviation proxy.
2. **Occupancy fraction** from the IDF's existing occupancy schedule must be part of every state snapshot.
3. **Rate-of-change limits** on setpoints, enforced in code, separate from and in addition to the comfort band.
4. **A real tool that parses EnergyPlus's own `.err` log** for severe errors/warnings and lets the agent react to it — this is explicit in the problem statement's Technical Core Requirement #2, not a nice-to-have.
5. **Look-ahead weather** (next 1–4 simulated hours), since the EPW file is fully known upfront and this is nearly free.
6. Every LLM decision returns a **setpoint + a natural-language rationale**, both logged.
7. A **safety/self-correction layer with a watchdog** that freezes to a safe baseline after repeated failures.

---

## 4. Architecture — Design Principles Applied

Name these explicitly in the architecture document (§14) and in code comments — they are part of what's being graded under "Code Elegance."

- **Single Responsibility per module.** Simulation I/O, state assembly, decision-making, safety validation, logging, and presentation are five separate concerns living in five separate packages. No module does two of these jobs.
- **Dependency Inversion via the Strategy pattern — this is the load-bearing architectural decision of the whole project.** The orchestration loop depends only on an abstract `SetpointPolicy` interface with one method, `decide(state) -> Action`. Phase 1 implements `FixedSchedulePolicy` (a dumb rule / literal baseline schedule). Phase 2 implements `LLMAgentPolicy`. **The orchestration loop, the actuator-writing code, the logging, and the safety layer are written exactly once, in Phase 1, and never touch again.** Swapping the brain is a one-line change of which policy object gets injected. This is what "de-risk the loop before adding intelligence" means in code, not just in planning prose.
- **Config over hardcoding.** Every tunable (comfort band, rate-of-change limit, decision cadence, watchdog threshold, COP, horizon length, model name) lives in one config object. Nothing is a magic number buried in a function.
- **Statelessness at the decision boundary.** Every call to the policy's `decide()` receives the *complete* current state (including rolling history and lookahead) and returns fresh. No hidden conversation memory, no growing context across decisions. This is a reliability requirement, not just a style preference — see §8.
- **Single source of truth for logging.** One structured event log (JSONL, one record per decision tick) is the only thing the dashboard reads from. The dashboard does not recompute or re-derive metrics independently — this guarantees the demo video, the dashboard, and the debugging output can never disagree with each other.
- **Fail-safe defaults / circuit breaker.** The watchdog is a literal circuit breaker: N consecutive invalid/failed decisions → trip → freeze to the safe fixed-schedule policy → log the trip event. Treat this as a first-class, demonstrable behavior (§11), not a hidden fallback.
- **Testability first.** Every layer except the EnergyPlus wrapper itself must be unit-testable with mocked inputs, with no simulation running. If you can't write a test for it without booting EnergyPlus, the module boundary is wrong.

### Layer diagram (dependency direction flows downward only)

```
Orchestration Loop  (owns the callback, the throttle counter, the wiring)
      │  depends on abstractions of:
      ▼
┌─────────────┬──────────────┬───────────────┬────────────┐
│ State Layer │ Policy Layer │ Safety Layer  │ Log Layer  │
│ (builds     │ (Strategy:   │ (validates +  │ (JSONL,    │
│ BuildingState│ Fixed | LLM) │ clamps +      │ single     │
│ each tick)  │              │ watchdog)     │ source of  │
│             │              │               │ truth)     │
└─────────────┴──────────────┴───────────────┴────────────┘
      ▲
      │  reads sensors from
┌─────────────┐
│ Simulation  │   EnergyPlus Python API — owns lifecycle,
│ Layer       │   callbacks, sensor/actuator handles
└─────────────┘

Dashboard Layer  →  reads ONLY from the event log. Nothing upstream
                     depends on the dashboard. It can be built,
                     broken, or rebuilt without touching the loop.
```

Nothing above the Simulation Layer imports EnergyPlus directly except the Simulation Layer itself. Nothing below the Orchestration Layer knows the Orchestration Layer exists.

---

## 5. Repository Structure

```
ecoloop/
├── config/
│   └── config.yaml
├── models/
│   ├── baseline.idf              # flat 22°C, no setback
│   └── agent_ready.idf           # same geometry/constructions, runtime-overridden setpoints
├── weather/
│   └── location.epw
├── src/ecoloop/
│   ├── simulation/
│   │   ├── runtime.py            # EnergyPlusRuntime: lifecycle, callback registration, handles
│   │   └── weather_lookahead.py  # pre-parsed EPW → indexed array, NOT read via EnergyPlus API
│   ├── state/
│   │   ├── schema.py             # BuildingState, HistoryPoint (pydantic)
│   │   └── builder.py            # StateBuilder: assembles BuildingState each decision tick
│   ├── policy/
│   │   ├── base.py               # SetpointPolicy Protocol — decide(state) -> Action
│   │   ├── fixed_schedule.py     # FixedSchedulePolicy (Phase 1 + baseline runs)
│   │   └── llm_agent.py          # LLMAgentPolicy (Phase 2): stateless prompt, tool loop
│   ├── safety/
│   │   └── validator.py          # SafetyValidator: bounds, rate-of-change, watchdog/circuit breaker
│   ├── tools/
│   │   ├── schemas.py            # tool JSON schemas, single definition used by both prompt + validator
│   │   └── error_parser.py       # parse_energyplus_errors implementation
│   ├── orchestration/
│   │   └── loop_controller.py    # throttle counter, wires callback → state → policy → safety → actuators → log
│   ├── logging/
│   │   └── event_log.py          # JSONL structured logger — single source of truth
│   ├── carbon/
│   │   └── intensity_profile.py  # representative real hourly profile, honestly labeled
│   └── dashboard/
│       └── app.py                # Streamlit — reads ONLY from event_log output
├── scripts/
│   ├── phase0_model_pressure_test.py   # standalone, no EnergyPlus, run FIRST
│   ├── run_baseline.py
│   ├── run_agent.py
│   └── compare_runs.py
├── tests/
│   ├── test_state_builder.py
│   ├── test_safety_validator.py
│   ├── test_policy_llm_mocked.py
│   └── test_weather_lookahead.py
├── docs/
│   └── architecture.md
├── logs/                          # gitignored
├── requirements.txt
└── README.md
```

---

## 6. Data Contracts

Define these as Pydantic models in `state/schema.py`. Every layer boundary in §4 communicates *only* through these — no raw dicts crossing module lines.

```python
class HistoryPoint(BaseModel):
    sim_timestamp: datetime
    zone_temp_c: float
    outdoor_temp_c: float
    energy_rate_w: float

class BuildingState(BaseModel):
    sim_timestamp: datetime
    zone_temps_c: dict[str, float]
    pmv: float
    occupancy_fraction: float
    heating_energy_rate_w: float
    cooling_energy_rate_w: float
    outdoor_temp_c: float
    lookahead_outdoor_temp_c: list[float]      # next 1-4 hrs, from pre-parsed EPW
    thermal_history: list[HistoryPoint]         # last 3-6 decision ticks
    carbon_intensity_gco2_kwh: float
    cumulative_energy_kwh: float
    current_heating_setpoint_c: float
    current_cooling_setpoint_c: float

class Action(BaseModel):
    heating_setpoint_c: float
    cooling_setpoint_c: float
    rationale: str                              # REQUIRED, never optional

class ValidationResult(BaseModel):
    accepted: bool
    final_heating_setpoint_c: float
    final_cooling_setpoint_c: float
    clamped: bool
    clamp_reason: str | None
    watchdog_tripped: bool

class DecisionLogRecord(BaseModel):
    decision_index: int
    sim_timestamp: datetime
    wall_clock_latency_s: float
    policy_name: str                             # "fixed_schedule" | "llm_agent"
    state: BuildingState
    proposed_action: Action
    validation_result: ValidationResult
    conservative_mode_active: bool                # see §11, error-tool "then what"
```

`DecisionLogRecord`, written to JSONL, is the **only** artifact the dashboard, the video narration, and post-hoc debugging are allowed to consume. If you find yourself computing a metric a second way anywhere else, stop — route it through this log instead.

---

## 7. LLM Tool Contracts

**Critical reliability decision — apply exactly:** the LLM does **not** call tools to *read* state. The complete `BuildingState` (current values + history + lookahead + carbon + occupancy + PMV) is serialized directly into the prompt every decision tick. Tools are reserved **only** for actions and validation, because every extra read-tool-call is an extra chance for a local model to fail structured output. This roughly halves round trips per decision versus a read/write tool split.

```python
TOOLS = [
  {
    "name": "set_heating_setpoint",
    "description": "Propose the next heating setpoint in Celsius.",
    "parameters": {"value_c": "float"}
  },
  {
    "name": "set_cooling_setpoint",
    "description": "Propose the next cooling setpoint in Celsius.",
    "parameters": {"value_c": "float"}
  },
  {
    "name": "validate_setpoints",
    "description": "Check proposed setpoints against comfort band and rate-of-change limits before committing.",
    "parameters": {"heating_c": "float", "cooling_c": "float"}
  },
  {
    "name": "parse_energyplus_errors",
    "description": "Read the current run's .err log and return structured severe errors and warnings.",
    "parameters": {}
  }
]
```

`validate_setpoints` **must call the exact same underlying function** that `safety/validator.py` uses for automatic enforcement — one implementation, two call sites (agent-invoked and always-on enforcement). If these ever diverge, the agent's tool will say "valid" while the enforcement layer silently overrides it, which reads as a bug in the demo. Log explicitly whenever the enforced value differs from the agent's request: `"agent proposed 24.5°C, clamped to 23.0°C (rate-of-change limit)"`. This log line is a good thing to show in the video — it's proof the safety layer works.

---

## 8. Configuration (single file, no magic numbers elsewhere)

```yaml
comfort_band_c: [21.0, 26.0]
max_delta_c_per_step: 1.5
decision_cadence_minutes: 60          # LLM invoked every Nth zone timestep, not every timestep
watchdog_max_consecutive_failures: 3
cop_cooling: 3.0                      # ASHRAE typical packaged/split AC range 2.5-4.0; 3.0 is conservative mid-range
heating_efficiency: 0.95              # adjust to actual heating plant type in the chosen IDF
simulated_horizon_days: 3             # 2-3 days max; confirm wall-clock budget before going higher
llm_model_name: "qwen2.5:7b-instruct" # preferred; llama3.1:8b-instruct as fallback; base mistral deprioritized
llm_max_retries: 2
llm_timeout_s: 8
baseline_setpoint_c: 22.0             # flat, 24/7, no setback — realistic legacy-BMS proxy
carbon_source_label: "Representative real hourly carbon intensity for [region], sourced from [Electricity Maps / WattTime]. Not timestamp-matched to the weather file year, because standard TMY files are composite."
```

**Wall-clock budget — do the arithmetic before committing to a horizon.** Hourly decisions over 3 simulated days = 72 decisions. At an 8s timeout with up to 2 retries worst case, cap per-decision latency and log it (`wall_clock_latency_s` in the schema above) so you have real numbers, not a guess, before deciding how much of the run can be shown live vs. pre-recorded.

---

## 9. Phased Build Plan — Definition of Done per Phase

Do not start a phase until the previous one's DoD is met. Produce a short Antigravity Artifact (walkthrough/screenshot) at the end of each phase for human review.

### Phase 0 — Model pressure test (standalone, no EnergyPlus, ~1-2 hrs — budget generously, don't rush)
- Script feeds the exact tool schema (§7) and 5-10 realistic synthetic `BuildingState` payloads to the chosen local model via Ollama.
- **DoD:** ≥90% of responses are schema-valid tool calls with a non-empty rationale. If below that, try the fallback model before proceeding. Do not wire this model into EnergyPlus until this bar is met.

### Phase 1 — Bare closed loop, `FixedSchedulePolicy` only (highest priority, targets 30% Integration)
- `EnergyPlusRuntime` + callback registration + actuator writes, using the dumb fixed-schedule policy.
- **DoD:**
  - Full `simulated_horizon_days` run completes with zero crashes.
  - Actuator handles verified non-negative (`get_actuator_handle` ≠ -1) and setpoints visibly move in the output — wrong handle names silently no-op, so confirm by inspecting output, not by assuming.
  - `Output:Variable` audit: every variable the code requests a handle for (PMV, zone temps, energy rates, etc.) has a matching `Output:Variable` request in the IDF. `get_variable_handle()` returns -1 silently otherwise — check every handle, not just PMV.
  - PMV sanity check: plot PMV across the run, confirm it varies believably in roughly [-2, +2], not flatlined at 0.
  - Baseline and agent-ready IDFs confirmed to use identical warmup-day handling.

### Phase 2 — Agent insertion (`LLMAgentPolicy`) + robustness
- Swap policy object only — orchestration code from Phase 1 is untouched, per §4's Strategy pattern.
- Throttle counter implemented (decision cadence from config, not every timestep).
- Stateless prompt construction confirmed — no growing message history across ticks.
- Retry/backoff on malformed tool output, bounded by `llm_max_retries` and `llm_timeout_s`.
- Full safety layer wired: comfort band + rate-of-change + watchdog circuit breaker.
- **DoD:** Full horizon run completes with the LLM policy active, zero crashes, measured `wall_clock_latency_s` recorded for every decision.

### Phase 3 — Metrics (targets 45%: Energy + Comfort)
- Baseline run (flat 22°C) and agent run, identical weather file, identical warmup.
- COP/efficiency conversion applied to report estimated electrical kWh, not raw thermal load.
- **DoD:** Dashboard shows total kWh + % reduction, comfort compliance % (including PMV stats), temperature traces, recovery/watchdog events — all sourced from the single JSONL log.
- Before finalizing: confirm the chosen weather window has real thermal stress (check EPW temperature profile — a mild shoulder-season window will show negligible savings regardless of agent quality).

### Phase 4 — Core requirement closure + high-ROI polish
- `parse_energyplus_errors` implemented and wired to the concrete "then what" behavior in §11.
- Look-ahead weather confirmed sourced from the pre-parsed EPW array, not any live EnergyPlus API (it has no forward-looking sensor).
- Decision rationales surfaced live on the dashboard.

### Phase 5 — Remaining score + submission
- Carbon intensity profile added with the exact honest label from §8.
- `docs/architecture.md` written (see §14).
- 3-minute video: live short segment + reference to the full pre-recorded run.
- Official presentation template filled in.

### Cut list if behind schedule (in order)
Real MCP server → multi-zone → Docker → operator override UI. Everything above Phase 4 items is protected; these are not.

---

## 10. Non-Functional Requirements

- **Reliability:** the loop must survive its full declared horizon with zero unhandled exceptions. Any exception path must be caught, logged, and resolved to a safe fallback — never a silent crash.
- **Observability:** every decision tick produces exactly one `DecisionLogRecord`. No metric is computed anywhere except by reading this log.
- **Latency budget:** log `wall_clock_latency_s` per decision from day one of Phase 2 — this is the number that determines your live-vs-recorded demo split, don't guess it.
- **Idempotency at the boundary:** `validate_setpoints` and the enforcement layer must be pure functions of `(proposed_action, current_state, config)` — no hidden mutable state beyond the watchdog's own failure counter.

---

## 11. The Error-Parsing Tool's "Then What" (concrete, not hand-wavy)

Fatal EnergyPlus errors typically kill the run before the loop can react — so in practice this tool is realistically catching **warnings** (unmet-hours, out-of-range setpoint warnings, sizing warnings), not fixing crashes. Implement one concrete, demonstrable behavior:

> If `parse_energyplus_errors` reports repeated unmet-hours or out-of-range warnings within a rolling window, set `conservative_mode_active = True` for the next M decisions: the policy is instructed (via an added line in the prompt / a tightened comfort band passed to `validate_setpoints`) to prefer setpoints closer to the center of the comfort band and reduce aggressiveness. Log the mode transition explicitly.

Have this exact scenario ready to trigger and narrate in the video and in Q&A — "what does the agent do when it sees an error" needs a real answer, not a pause.

---

## 12. Guardrails — Do Not Silently Change These

- Do not implement state-reading as LLM tool calls — inject full state into the prompt (§7).
- Do not accumulate conversation history across decision ticks — every call is stateless.
- Do not report thermal load as "kWh" without applying and disclosing the COP/efficiency conversion in §8.
- Do not claim MCP-server-alignment anywhere (docs, video, code comments) unless a real MCP server is actually implemented and running — default to plain custom tool-calling functions, which the problem statement explicitly permits.
- Do not read look-ahead weather from any live EnergyPlus sensor API — it doesn't expose forward time. Use the pre-parsed EPW array only.
- Do not extend `simulated_horizon_days` beyond 3 without recomputing the wall-clock budget in §8.
- Do not let `validate_setpoints` (the tool) and the safety enforcement layer diverge into two implementations.
- Do not proceed past Phase 0 if the tool-calling reliability bar isn't met — swap models, don't lower the bar.

---

## 13. Honest Data & Claims Policy

| Component | Source | Label as |
|---|---|---|
| Building physics | EnergyPlus | Real |
| Weather | Real EPW (prefer AMY for a specific year/city if easily available; TMY acceptable) | Real |
| Zone temps, PMV, energy rates | Live EnergyPlus output | Real |
| Carbon intensity | Representative real hourly profile (Electricity Maps / WattTime) | Real, explicitly labeled "representative," **not** year-matched — TMY files are composite and a stronger claim doesn't survive scrutiny |
| LLM decisions + rationale | Local open-source model, live | Real |
| Reported kWh | EnergyPlus thermal output × stated COP/efficiency | Real physics + disclosed conversion assumption |

No synthetic sensor streams, no placeholder occupancy, no invented numbers anywhere in the dashboard, doc, or video.

---

## 14. Architecture Document Requirements (`docs/architecture.md`)

Must cover, concretely (not generically):
- Tool-calling architecture and why reads are injected vs. tool-called (§7 reasoning).
- The Strategy-pattern policy swap (§4) — this is your strongest "code elegance" evidence, state it explicitly.
- Latency management: throttle cadence, retry/backoff bounds, measured wall-clock numbers from your actual runs.
- Long-log handling: how `parse_energyplus_errors` works and its concrete conservative-mode behavior (§11).
- Safety design: comfort band, rate-of-change clamp and the explicit tradeoff it makes with morning-warmup responsiveness, watchdog circuit breaker.
- COP assumption and one-sentence justification (§8).

---

## 15. Deliverables Checklist (map back to submission requirements)

- [ ] GitHub repo — source code, orchestration, communication bus, all in one clean codebase
- [ ] Baseline IDF + agent-ready IDF (+ any runtime-modified intermediates)
- [ ] Quantitative dashboard — baseline vs. agent, % kWh reduction, comfort compliance
- [ ] `docs/architecture.md` per §14
- [ ] 3-minute demo video — live segment + reference to full recorded run, per §9 Phase 5
- [ ] Presentation using the official template

---

## First Action Requested From You (the agent)

1. Read this entire file.
2. Produce an implementation-plan Artifact covering **Phase 0 and Phase 1 only**.
3. Stop and wait for confirmation before writing any Phase 2 code.
4. Start Phase 0 with `scripts/phase0_model_pressure_test.py` — no EnergyPlus code until its DoD is met.
