from __future__ import annotations

from importlib import import_module
from typing import Callable

STATE_MODULES: dict[str, tuple[str, str]] = {
    "AL": ("states.alabama", "run_alabama"),
    "AK": ("states.alaska", "run_alaska"),
    "AR": ("states.arkansas", "run_arkansas"),
    "CA": ("states.california", "run_california"),
    "CO": ("states.colorado", "run_colorado"),
    "CT": ("states.connecticut", "run_connecticut"),
    "DE": ("states.delaware", "run_delaware"),
    "ID": ("states.idaho", "run_idaho"),
    "IL": ("states.illinois", "run_illinois"),
    "IN": ("states.indiana", "run_indiana"),
}


def get_state_runner(state_code: str) -> Callable:
    code = (state_code or "").upper()
    if code not in STATE_MODULES:
        raise ValueError(f"No state module registered for: {state_code}")

    module_path, function_name = STATE_MODULES[code]
    module = import_module(module_path)
    runner = getattr(module, function_name, None)
    if runner is None:
        raise AttributeError(f"Runner '{function_name}' not found in module '{module_path}'")
    return runner
