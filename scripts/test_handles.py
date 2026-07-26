import sys
import os

sys.path.insert(0, r"C:\EnergyPlusV24-2-0")
from pyenergyplus.api import EnergyPlusAPI

def callback_function(state_arg):
    if not api.exchange.api_data_fully_ready(state_arg):
        return

    h_temp = api.exchange.get_variable_handle(state_arg, "Zone Air Temperature", "SPACE1-1")
    h_pmv = api.exchange.get_variable_handle(state_arg, "Zone Thermal Comfort Fanger Model PMV", "SPACE1-1 People 1")
    h_heat_sp = api.exchange.get_actuator_handle(state_arg, "Zone Temperature Control", "Heating Setpoint", "SPACE1-1")
    h_cool_sp = api.exchange.get_actuator_handle(state_arg, "Zone Temperature Control", "Cooling Setpoint", "SPACE1-1")

    print("==================================================")
    print("REAL ENERGYPLUS API HANDLE INTEGERS RETURNED:")
    print(f"- Zone Air Temperature Handle:               {h_temp}")
    print(f"- Zone Thermal Comfort Fanger PMV Handle:    {h_pmv}")
    print(f"- Heating Setpoint Actuator Handle:          {h_heat_sp}")
    print(f"- Cooling Setpoint Actuator Handle:          {h_cool_sp}")
    print("==================================================")

    api.runtime.stop_simulation(state_arg)

api = EnergyPlusAPI()
state = api.state_manager.new_state()

api.runtime.callback_begin_zone_timestep_before_init_heat_balance(state, callback_function)

cmd_args = [
    "-d", "logs/ep_handles_out",
    "-w", "weather/location.epw",
    "models/baseline.idf"
]

api.runtime.run_energyplus(state, cmd_args)
api.state_manager.delete_state(state)
