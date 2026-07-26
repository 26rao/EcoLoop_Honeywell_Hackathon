import re

def update_people_object(idf_path):
    with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Define clean People object with Fanger thermal comfort enabled
    new_people = """People,
    SPACE1-1 People 1,       !- Name
    SPACE1-1,                !- Zone or ZoneList or Space or SpaceList Name
    OCCUPY-1,                !- Number of People Schedule Name
    people,                  !- Number of People Calculation Method
    11,                      !- Number of People
    ,                        !- People per Floor Area {person/m2}
    ,                        !- Floor Area per Person {m2/person}
    0.3,                     !- Fraction Radiant
    AUTOCALCULATE,           !- Sensible Heat Fraction
    Activity Schedule 1,     !- Activity Level Schedule Name
    3.82E-8,                 !- Carbon Dioxide Generation Rate {m3/s-W}
    No,                      !- Enable ASHRAE 55 Warning
    ZoneAveraged,            !- Mean Radiant Temperature Calculation Type
    ,                        !- Surface Name/Angle Factor List Name
    ,                        !- Work Efficiency Schedule Name
    ClothingInsulationSchedule, !- Clothing Insulation Calculation Method
    ,                        !- Clothing Insulation Calculation Method Schedule Name
    Clothing Schedule 1,     !- Clothing Insulation Schedule Name
    Air Velocity Schedule 1,  !- Air Velocity Schedule Name
    Fanger;                  !- Thermal Comfort Model 1 Type
"""
    # Replace the existing SPACE1-1 People 1 block
    pattern = r"People,\s*SPACE1-1 People 1,[\s\S]*?;"
    updated_content = re.sub(pattern, new_people.strip(), content)

    with open(idf_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

update_people_object("models/baseline.idf")
update_people_object("models/agent_ready.idf")
print("Successfully enabled Fanger Thermal Comfort Model in baseline.idf and agent_ready.idf.")
