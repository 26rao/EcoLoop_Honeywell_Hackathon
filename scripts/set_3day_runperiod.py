import re

three_day_runperiod = """
RunPeriod,
    Summer3DayHorizon,       !- Name
    7,                       !- Begin Month
    7,                       !- Begin Day of Month
    2015,                    !- Begin Year
    7,                       !- End Month
    9,                       !- End Day of Month
    2015,                    !- End Year
    Tuesday,                 !- Day of Week for Start Day
    Yes,                     !- Use Weather File Holidays and Special Days
    Yes,                     !- Use Weather File Daylight Saving Period
    No,                      !- Apply Weekend Holiday Rule
    Yes,                     !- Use Weather File Rain Indicators
    Yes;                     !- Use Weather File Wind Speeds
"""

def update_runperiod(idf_path):
    with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Remove all existing RunPeriod objects
    pattern = r"RunPeriod,\s*[\s\S]*?;"
    content_cleaned = re.sub(pattern, "", content)

    # Append single 3-day RunPeriod
    content_final = content_cleaned.strip() + "\n" + three_day_runperiod

    with open(idf_path, 'w', encoding='utf-8') as f:
        f.write(content_final)

update_runperiod("models/baseline.idf")
update_runperiod("models/agent_ready.idf")
print("Set single 3-day RunPeriod (July 7 to July 9) in baseline.idf and agent_ready.idf.")
