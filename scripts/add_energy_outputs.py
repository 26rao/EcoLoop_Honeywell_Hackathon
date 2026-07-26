def add_outputs(idf_path):
    with open(idf_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    new_vars = """
Output:Variable,*,Zone Ideal Loads Supply Air Total Heating Rate,timestep;
Output:Variable,*,Zone Ideal Loads Supply Air Total Cooling Rate,timestep;
"""

    if "Zone Ideal Loads Supply Air Total Heating Rate" not in content:
        content += new_vars

    with open(idf_path, "w", encoding="utf-8") as f:
        f.write(content)

add_outputs("models/baseline.idf")
add_outputs("models/agent_ready.idf")
print("Added energy rate Output:Variable declarations to baseline and agent IDFs.")
