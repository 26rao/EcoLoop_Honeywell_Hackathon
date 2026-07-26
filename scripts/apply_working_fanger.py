import re

def update_people(idf_path):
    with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

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
    ActSchd,                 !- Activity Level Schedule Name
    ,                        !- Carbon Dioxide Generation Rate {m3/s-W}
    No,                      !- Enable ASHRAE 55 Comfort Warnings
    EnclosureAveraged,       !- Mean Radiant Temperature Calculation Type
    ,                        !- Surface Name/Angle Factor List Name
    ,                        !- Work Efficiency Schedule Name
    ,                        !- Clothing Insulation Calculation Method
    ,                        !- Clothing Insulation Calculation Method Schedule Name
    ,                        !- Clothing Insulation Schedule Name
    ,                        !- Air Velocity Schedule Name
    FANGER;                  !- Thermal Comfort Model 1 Type
"""

    pattern = r"People,\s*SPACE1-1 People 1,[\s\S]*?;"
    updated = re.sub(pattern, new_people.strip(), content)

    with open(idf_path, 'w', encoding='utf-8') as f:
        f.write(updated)

update_people("models/baseline.idf")
update_people("models/agent_ready.idf")
print("Updated People objects with blank clothing insulation method and FANGER model.")
