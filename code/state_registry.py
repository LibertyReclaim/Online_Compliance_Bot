from __future__ import annotations

from typing import Callable

# Placeholder registry for future state modules.
# Example future entry:
# STATE_MODULES["CA"] = "states.california:run_california"
STATE_MODULES: dict[str, str] = {}


def get_state_runner(state_code: str) -> Callable:
    code = (state_code or "").upper()
    if code not in STATE_MODULES:
        raise NotImplementedError(
            f"No state module registered for '{code}'. "
            "Add a state runner under code/states and register it in state_registry.py."
        )

    # Placeholder for future dynamic import implementation when modules are added.
    raise NotImplementedError("State registry import wiring will be enabled when state modules are added.")
