import os
import re
from pathlib import Path
from typing import Dict, Any, List

class EnergyPlusErrorParser:
    """Phase 4 Error Parser & Conservative Mode Trigger."""

    def __init__(self, err_file_path: str = "logs/real_agent_ep_out/eplusout.err"):
        self.err_file_path = Path(err_file_path)
        self.unmet_warning_count = 0
        self.conservative_mode_active = False

    def parse_err_file(self) -> Dict[str, Any]:
        if not self.err_file_path.exists():
            return {
                "file_found": False,
                "warnings": 0,
                "severe_errors": 0,
                "unmet_hours_warnings": 0,
                "conservative_mode_triggered": False
            }

        with open(self.err_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        warnings = len(re.findall(r"\*\* Warning \*\*", content))
        severe_errors = len(re.findall(r"\*\* Severe  \*\*", content))
        unmet_warnings = len(re.findall(r"unmet|temperature out of bounds|comfort warning", content, re.IGNORECASE))

        self.unmet_warning_count = unmet_warnings

        # Trigger conservative mode if 2 or more warnings detected
        if unmet_warnings >= 2 or warnings >= 3:
            self.conservative_mode_active = True

        return {
            "file_found": True,
            "warnings": warnings,
            "severe_errors": severe_errors,
            "unmet_hours_warnings": unmet_warnings,
            "conservative_mode_triggered": self.conservative_mode_active
        }
