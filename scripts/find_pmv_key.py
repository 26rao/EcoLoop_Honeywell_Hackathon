import sys
import os

sys.path.insert(0, r"C:\EnergyPlusV24-2-0")
from pyenergyplus.api import EnergyPlusAPI

def callback_function(state_arg):
    if not api.exchange.api_data_fully_ready(state_arg):
        return

    keys = ["*", "SPACE1-1", "SPACE1-1 PEOPLE 1", "SPACE1-1 People 1", "PEOPLE 1", "People 1", "OFFICE PEOPLE"]
    for k in keys:
        h = api.exchange.get_variable_handle(state_arg, "Zone Thermal Comfort Fanger Model PMV", k)
        if h != -1:
            print(f"FOUND VALID PMV HANDLE FOR KEY '{k}': {h}")
        else:
            print(f"Key '{k}' returned -1")

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
