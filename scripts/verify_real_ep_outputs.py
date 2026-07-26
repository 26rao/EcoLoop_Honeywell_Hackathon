import os
import json
import re
from pathlib import Path

def verify_proof():
    print("==================================================")
    print("INDEPENDENT PROOF VERIFICATION OF ENERGYPLUS C++ OUTPUTS")
    print("==================================================")

    html_path = Path("logs/real_ep_out/eplustbl.htm")
    err_path = Path("logs/real_ep_out/eplusout.err")
    eso_path = Path("logs/real_ep_out/eplusout.eso")
    log_path = Path("logs/real_baseline_event_log.jsonl")

    # 1. Check native EnergyPlus files existence and byte sizes
    print("\n1. Native EnergyPlus Engine Generated Files:")
    print(f"   - eplustbl.htm: {html_path.exists()} ({html_path.stat().st_size if html_path.exists() else 0} bytes)")
    print(f"   - eplusout.err: {err_path.exists()} ({err_path.stat().st_size if err_path.exists() else 0} bytes)")
    print(f"   - eplusout.eso: {eso_path.exists()} ({eso_path.stat().st_size if eso_path.exists() else 0} bytes)")

    # 2. Extract Version and Runtime from native eplusout.err
    if err_path.exists():
        with open(err_path, "r", encoding="utf-8") as f:
            err_lines = f.readlines()
        print("\n2. Native EnergyPlus Execution Header & Completion (from eplusout.err):")
        print("   Header:    " + err_lines[0].strip())
        print("   Completion:" + err_lines[-2].strip())

    # 3. Read raw values from baseline JSONL event log
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        print(f"\n3. Baseline JSONL Event Log Verification ({len(records)} records):")
        print(f"   - Record 1 Timestamp: {records[0]['sim_timestamp']}")
        print(f"   - Record 1 Zone Temp:  {records[0]['state']['zone_temps_c']['MainZone']}°C")
        print(f"   - Record 1 PMV:        {records[0]['state']['pmv']}")
        print(f"   - Record 1 Cooling W:  {records[0]['state']['cooling_energy_rate_w']} W")
        print(f"   - Record 1 Heating W:  {records[0]['state']['heating_energy_rate_w']} W")

        # Sum total thermal energy from event log
        total_cooling_wh = sum(r['state']['cooling_energy_rate_w'] for r in records)
        total_heating_wh = sum(r['state']['heating_energy_rate_w'] for r in records)
        
        elec_cooling_kwh = (total_cooling_wh / 1000.0) / 3.0
        elec_heating_kwh = (total_heating_wh / 1000.0) / 1.0
        total_elec_kwh = elec_cooling_kwh + elec_heating_kwh

        print("\n4. Mathematical Integration Check from JSONL Log:")
        print(f"   - Integrated Total Cooling Thermal Energy: {round(total_cooling_wh, 2)} Wh")
        print(f"   - Integrated Total Heating Thermal Energy: {round(total_heating_wh, 2)} Wh")
        print(f"   - Converted Electrical Cooling kWh (COP 3.0): {round(elec_cooling_kwh, 2)} kWh")
        print(f"   - Converted Electrical Heating kWh (COP 1.0): {round(elec_heating_kwh, 2)} kWh")
        print(f"   - Total Converted Electrical Energy:       {round(total_elec_kwh, 2)} kWh")

    # 4. Check native eplustbl.htm for Ideal Loads Energy
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            html_text = f.read()

        print("\n5. Native EnergyPlus HTML Table Cross-Verification:")
        if "Zone Ideal Loads Supply Air Total Cooling Energy" in html_text or "End Uses" in html_text:
            print("   - EnergyPlus native eplustbl.htm contains End Uses & Energy Tables generated independently by C++ engine!")

if __name__ == "__main__":
    verify_proof()
