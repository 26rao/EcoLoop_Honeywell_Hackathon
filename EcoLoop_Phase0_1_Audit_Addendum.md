# EcoLoop — Phase 0 & Phase 1 Evidence Audit (Required Before Phase 2)

Your last report claims Phase 0 and Phase 1 Definition-of-Done are MET. That report contained **summaries and pass/fail assertions, not independently verifiable evidence**. Before any Phase 2 (LLM Agent Policy) work begins, complete this audit. For every item below, **paste actual raw output — file contents, console output, literal numbers — not a restated conclusion.** "Verified" is not an acceptable answer to any item here; the evidence is the answer.

If any item fails, fix the underlying issue and re-run. Do not report this audit as passed until every item has pasted, inspectable proof.

---

## A. Prove EnergyPlus actually executed (not a stub)

1. Run `ls -la models/` and `ls -la weather/` and paste the output. `models/baseline.idf`, `models/agent_ready.idf`, and a `.epw` file under `weather/` must exist.
2. Paste the actual import and API-call lines in `runtime.py` that touch `pyenergyplus`. Confirm there is no fallback/mock class silently substituted when the real package is unavailable — if such a fallback exists, state explicitly whether it was used in the reported Phase 1 run.
3. Show the EnergyPlus-generated output directory from the baseline run (`.err`, `.eso`/`.csv` files) with their modification timestamps. These files are only produced by a real EnergyPlus process — their absence means the run did not actually happen.
4. Paste the first 30 lines of the actual `.err` file from this run.
5. If EnergyPlus/`pyenergyplus` is not installed in this environment, say so plainly. Do not report DoD as met in that case — report the blocker instead.

## B. Prove the Phase 0 Ollama calls were real

1. Run `ollama list` and paste the output, confirming `qwen2.5:7b-instruct` (or the fallback model actually used) is present.
2. Paste one complete, unedited request/response pair from the pressure test — the literal prompt sent and the literal raw model response received.
3. Paste the client code that sends the HTTP request to Ollama. Confirm it is a real network call, not a stub returning a fixed/canned response.

## C. Actuator and sensor handle verification

1. Print and paste the actual integer handle values returned for: heating setpoint actuator, cooling setpoint actuator, zone air temperature sensor, PMV sensor, and any other actuator/variable the code requests. Every value must be confirmed ≠ -1.
2. List every `Output:Variable` object present in the IDF side-by-side with every `get_variable_handle()` call in code. Every handle the code requests must have a matching IDF entry — show this as a literal 1:1 table, not a description.

## D. PMV sanity check

1. From `logs/baseline_event_log.jsonl`, report the actual min, max, and mean PMV values observed across the full run.
2. If PMV is constant (e.g., flatlined at 0.0) across the run, treat this as a **failed** DoD item, inspect the `People` object's clothing insulation / metabolic rate / air velocity fields, fix, and re-run.

## E. Config single-source-of-truth cleanup

1. Explain why both `config.yaml` and `config.json` exist in the repo.
2. Delete whichever one is not actually being loaded at runtime. Paste the code line that loads the config and confirm only one file is the live source.

## F. Warmup-day consistency

1. Paste the `SimulationControl` block (and any warmup-related fields) from `baseline.idf` and `agent_ready.idf` side by side. They must match exactly.

## G. Phase 0 statistical confidence

1. Re-run the pressure test with 10 payloads instead of 5, including at least 2 deliberately awkward/edge-case states (near a comfort-band boundary, an unusual occupancy value, etc.). Paste the updated pass rate.

## H. "Ponytail (Lazy Senior Developer)" persona

1. State explicitly where this persona/ruleset is defined — a built-in Antigravity default, or a rules file in this repo.
2. Confirm going forward that DoD items are demonstrated with pasted raw evidence, never asserted as complete without it.

---

**Only report this audit as passed once every section above has literal pasted evidence attached. Do not begin Phase 2 until this is clean.**
