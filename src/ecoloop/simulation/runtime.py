import sys
import os
import logging
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger("EcoLoop.Runtime")

class EnergyPlusRuntime:
    """Wrapper for EnergyPlus Python API runtime execution, handles management, and callback registration."""

    def __init__(self, idf_path: str, epw_path: str, output_dir: str = "logs/ep_out", ep_install_dir: str = r"C:\EnergyPlusV24-2-0"):
        self.idf_path = idf_path
        self.epw_path = epw_path
        self.output_dir = output_dir
        self.ep_install_dir = ep_install_dir

        self.api = None
        self.state = None
        self.handles: Dict[str, int] = {}
        self._try_import_api()

    def _try_import_api(self):
        # Dynamically append EnergyPlus installation directory to sys.path if present
        if self.ep_install_dir and os.path.exists(self.ep_install_dir) and self.ep_install_dir not in sys.path:
            sys.path.insert(0, self.ep_install_dir)

        try:
            from pyenergyplus.api import EnergyPlusAPI
            self.api = EnergyPlusAPI()
            logger.info(f"Successfully imported pyenergyplus.api.EnergyPlusAPI from {self.ep_install_dir}")
        except ImportError as e:
            logger.warning(f"pyenergyplus API import failed ({e}). Running in standalone mock mode.")

    def run_simulation(self, callback_fn: Optional[Callable] = None):
        """Runs the EnergyPlus simulation or mock loop if pyenergyplus is unavailable."""
        if self.api:
            self.state = self.api.state_manager.new_state()
            if callback_fn:
                self.api.runtime.callback_begin_system_timestep_before_predictor(self.state, callback_fn)

            cmd_args = [
                "-d", self.output_dir,
                "-w", self.epw_path,
                self.idf_path
            ]
            exit_code = self.api.runtime.run_energyplus(self.state, cmd_args)
            self.api.state_manager.delete_state(self.state)
            return exit_code
        else:
            logger.info("Executing simulation loop via fallback mock engine...")
            return 0
