import inspect
from typing import Any


def is_zero_arg_callable(value: Any) -> bool:
    """
    Return True if `value` is callable and can be called with no arguments.
    """
    if not callable(value):
        return False

    try:
        sig = inspect.signature(value)
    except (TypeError, ValueError):
        # Builtins / C-extensions may not have signatures
        return False

    for p in sig.parameters.values():
        if (
            p.default is inspect.Parameter.empty
            and p.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ):
            return False

    return True

def call_if_zero_arg(value: Any):
    """
    Call value if it is a zero-arg callable, otherwise return as-is.
    """
    return value() if is_zero_arg_callable(value) else value