import os
import json
from pathlib import Path
from typing import List
from ecoloop.state.schema import DecisionLogRecord

class EventLogger:
    """Structured JSONL Logger for EcoLoop decisions - single source of truth."""

    def __init__(self, log_file_path: str = "logs/event_log.jsonl"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, record: DecisionLogRecord):
        """Appends a single DecisionLogRecord as a JSON line."""
        record_dict = json.loads(record.model_dump_json())
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_dict) + "\n")

    def read_all_records(self) -> List[dict]:
        """Reads all JSON records from the log file."""
        records = []
        if not self.log_file_path.exists():
            return records
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
