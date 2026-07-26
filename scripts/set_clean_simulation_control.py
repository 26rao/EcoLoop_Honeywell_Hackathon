import re

sim_control_text = """
SimulationControl,
    No,                      !- Do Zone Sizing Calculation
    No,                      !- Do System Sizing Calculation
    No,                      !- Do Plant Sizing Calculation
    No,                      !- Run Simulation for Sizing Periods
    Yes,                     !- Run Simulation for Weather File Run Periods
    No,                      !- Do HVAC Sizing Simulation for Sizing Periods
    1;                       !- Maximum Number of HVAC Sizing Simulation Passes
"""

def update_sim_control(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    pattern = r"SimulationControl,\s*[\s\S]*?;"
    updated = re.sub(pattern, sim_control_text.strip(), content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)

update_sim_control("models/baseline.idf")
update_sim_control("models/agent_ready.idf")
print("Updated SimulationControl to run ONLY Weather File Run Period (Sizing periods disabled).")
