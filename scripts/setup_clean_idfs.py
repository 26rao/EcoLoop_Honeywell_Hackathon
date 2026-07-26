import shutil

src_idf = r"C:\EnergyPlusV24-2-0\ExampleFiles\5Zone_IdealLoadsAirSystems_ReturnPlenum.idf"
shutil.copy(src_idf, "models/baseline.idf")

with open("models/baseline.idf", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Replace "People," blocks to add "Fanger" at the end of People objects or append Output:Variable
# In 5Zone_IdealLoadsAirSystems_ReturnPlenum.idf, let's update People objects to include Fanger model type
updated_content = content.replace("ZoneAveraged,", "EnclosureAveraged,")
updated_content += "\nOutput:Variable,*,Zone Thermal Comfort Fanger Model PMV,timestep;\n"
updated_content += "Output:Variable,*,Zone Air Temperature,timestep;\n"

with open("models/baseline.idf", "w", encoding="utf-8") as f:
    f.write(updated_content)

shutil.copy("models/baseline.idf", "models/agent_ready.idf")
print("Clean models/baseline.idf and models/agent_ready.idf setup completed.")
