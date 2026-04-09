from __future__ import annotations

from importlib import import_module
from typing import Callable

# State registry.
# Key: state code, Value: (<module path>, <runner function>)
STATE_MODULES: dict[str, tuple[str, str]] = {
    "NY": ("states.newyork", "run"),
}


def get_state_runner(state_code: str) -> Callable:
    code = (state_code or "").upper()
    if code not in STATE_MODULES:
        raise NotImplementedError(
            f"No state module registered for '{code}'. "
            "Add a state runner under code/states and register it in state_registry.py."
        )

    module_path, function_name = STATE_MODULES[code]
    module = import_module(module_path)
    runner = getattr(module, function_name, None)
    if runner is None:
        raise AttributeError(f"Runner '{function_name}' not found in module '{module_path}'")
    return runner
