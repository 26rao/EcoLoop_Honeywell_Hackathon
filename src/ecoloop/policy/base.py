from typing import Protocol
from ecoloop.state.schema import BuildingState, Action

class SetpointPolicy(Protocol):
    """Protocol / Interface for Setpoint Decision Policies (Strategy Pattern)."""

    name: str

    def decide(self, state: BuildingState) -> Action:
        """Given current building state, returns proposed Action (heating & cooling setpoints + rationale)."""
        ...
