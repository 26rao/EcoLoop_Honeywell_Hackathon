import json
from pathlib import Path

def recompute_clean_comparison():
    print("==================================================")
    print("ECOLOOP CLEAN COMPARISON RE-COMPUTATION & CROSS-CHECK")
    print("==================================================")

    base_path = Path("logs/real_baseline_event_log.jsonl")
    agent_path = Path("logs/real_agent_event_log.jsonl")

    # 1. Print & Paste Head/Tail of both log files
    with open(base_path, "r", encoding="utf-8") as f:
        base_lines = [l.strip() for l in f if l.strip()]
    with open(agent_path, "r", encoding="utf-8") as f:
        agent_lines = [l.strip() for l in f if l.strip()]

    print(f"\n1. LOG FILE LINE COUNTS:")
    print(f"   - Baseline Log: {len(base_lines)} lines")
    print(f"   - Agent Log:    {len(agent_lines)} lines")

    base_records = [json.loads(l) for l in base_lines]
    agent_records = [json.loads(l) for l in agent_lines]

    print("\n2. BASELINE LOG HEAD & TAIL:")
    b0 = base_records[0]
    b_end = base_records[-1]
    print(f"   First Line [1]: Policy={b0['policy_name']} | Time={b0['sim_timestamp']} | Heat={b0['validation_result']['final_heating_setpoint_c']}°C | Cool={b0['validation_result']['final_cooling_setpoint_c']}°C | PMV={b0['state']['pmv']} | CoolW={b0['state']['cooling_energy_rate_w']}W")
    print(f"   Last Line [73]: Policy={b_end['policy_name']} | Time={b_end['sim_timestamp']} | Heat={b_end['validation_result']['final_heating_setpoint_c']}°C | Cool={b_end['validation_result']['final_cooling_setpoint_c']}°C | PMV={b_end['state']['pmv']} | CoolW={b_end['state']['cooling_energy_rate_w']}W")

    print("\n3. AGENT LOG HEAD & TAIL:")
    a0 = agent_records[0]
    a_end = agent_records[-1]
    print(f"   First Line [1]: Policy={a0['policy_name']} | Time={a0['sim_timestamp']} | Heat={a0['validation_result']['final_heating_setpoint_c']}°C | Cool={a0['validation_result']['final_cooling_setpoint_c']}°C | PMV={a0['state']['pmv']} | CoolW={a0['state']['cooling_energy_rate_w']}W")
    print(f"   Last Line [73]: Policy={a_end['policy_name']} | Time={a_end['sim_timestamp']} | Heat={a_end['validation_result']['final_heating_setpoint_c']}°C | Cool={a_end['validation_result']['final_cooling_setpoint_c']}°C | PMV={a_end['state']['pmv']} | CoolW={a_end['state']['cooling_energy_rate_w']}W")

    # 4. Integrate Electrical kWh & Comfort Compliance for Baseline
    base_cool_wh = sum(r['state']['cooling_energy_rate_w'] for r in base_records)
    base_heat_wh = sum(r['state']['heating_energy_rate_w'] for r in base_records)
    base_cool_kwh = (base_cool_wh / 1000.0) / 3.0
    base_heat_kwh = (base_heat_wh / 1000.0) / 1.0
    base_total_kwh = base_cool_kwh + base_heat_kwh

    base_pmvs = [r['state']['pmv'] for r in base_records]
    base_compliant = sum(1 for p in base_pmvs if -0.5 <= p <= 0.5)
    base_comfort_pct = (base_compliant / len(base_pmvs)) * 100.0

    # 5. Integrate Electrical kWh & Comfort Compliance for Agent
    agent_cool_wh = sum(r['state']['cooling_energy_rate_w'] for r in agent_records)
    agent_heat_wh = sum(r['state']['heating_energy_rate_w'] for r in agent_records)
    agent_cool_kwh = (agent_cool_wh / 1000.0) / 3.0
    agent_heat_kwh = (agent_heat_wh / 1000.0) / 1.0
    agent_total_kwh = agent_cool_kwh + agent_heat_kwh

    agent_pmvs = [r['state']['pmv'] for r in agent_records]
    agent_compliant = sum(1 for p in agent_pmvs if -0.5 <= p <= 0.5)
    agent_comfort_pct = (agent_compliant / len(agent_pmvs)) * 100.0

    savings_pct = ((base_total_kwh - agent_total_kwh) / base_total_kwh) * 100.0

    print("\n4. INTEGRATED COMPARISON RESULTS (DIRECTLY FROM COMPLETE 73-RECORD LOGS):")
    print(f"   Baseline Electrical Energy: {round(base_total_kwh, 2)} kWh (Cooling: {round(base_cool_kwh, 2)} kWh, Heating: {round(base_heat_kwh, 2)} kWh)")
    print(f"   Baseline PMV Compliance:    {round(base_comfort_pct, 1)}% (PMV Range: [{min(base_pmvs)}, {max(base_pmvs)}], Mean: {round(sum(base_pmvs)/len(base_pmvs), 2)})")
    print(f"   --------------------------------------------------")
    print(f"   Agent Electrical Energy:    {round(agent_total_kwh, 2)} kWh (Cooling: {round(agent_cool_kwh, 2)} kWh, Heating: {round(agent_heat_kwh, 2)} kWh)")
    print(f"   Agent PMV Compliance:       {round(agent_comfort_pct, 1)}% (PMV Range: [{min(agent_pmvs)}, {max(agent_pmvs)}], Mean: {round(sum(agent_pmvs)/len(agent_pmvs), 2)})")
    print(f"   --------------------------------------------------")
    print(f"   Net Energy Reduction:       {round(savings_pct, 1)}% Energy Savings")

if __name__ == "__main__":
    recompute_clean_comparison()
