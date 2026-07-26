import re

schedules_text = """
Schedule:Compact,
    WORK_EFF_SCH,
    Fraction,
    Through: 12/31,
    For: AllDays,
    Until: 24:00, 0.0;

Schedule:Compact,
    CLOTHING_SCH,
    Any Number,
    Through: 12/31,
    For: AllDays,
    Until: 24:00, 1.0;

Schedule:Compact,
    AIR_VELO_SCH,
    Any Number,
    Through: 12/31,
    For: AllDays,
    Until: 24:00, 0.13;
"""

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
    WORK_EFF_SCH,            !- Work Efficiency Schedule Name
    ClothingInsulationSchedule, !- Clothing Insulation Calculation Method
    ,                        !- Clothing Insulation Calculation Method Schedule Name
    CLOTHING_SCH,            !- Clothing Insulation Schedule Name
    AIR_VELO_SCH,            !- Air Velocity Schedule Name
    FANGER;                  !- Thermal Comfort Model 1 Type
"""

def update_idf(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    pattern = r"People,\s*SPACE1-1 People 1,[\s\S]*?;"
    updated = re.sub(pattern, new_people.strip(), content)
    updated += "\n" + schedules_text

    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)

update_idf("models/baseline.idf")
update_idf("models/agent_ready.idf")
print("Added thermal comfort schedules and updated People objects.")
