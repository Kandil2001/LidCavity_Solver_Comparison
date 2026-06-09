from __future__ import annotations

# -----------------------------------------------------------------------------


def lower(s: str) -> str:
    return str(s).lower()


def upper(s: str) -> str:
    return str(s).upper()


def normalize_implementation(s: str) -> str:
    s = lower(s)
    vectorized_aliases = {
        "serial_python_vectorized", "python_vectorized", "py_vectorized",
        "vectorized_python", "numpy", "python_numpy", "serial_python",
        "python", "py", "serial", "vectorized",
    }
    looped_aliases = {
        "serial_python_looped", "python_looped", "py_looped",
        "looped_python", "loop", "looped", "loops",
    }
    if s in vectorized_aliases:
        return "serial_python_vectorized"
    if s in looped_aliases:
        return "serial_python_looped"
    raise ValueError("Unknown implementation: %s (use serial_python_vectorized or serial_python_looped)" % s)


def is_looped_implementation(implementation: str) -> bool:
    return normalize_implementation(implementation) == "serial_python_looped"


# -----------------------------------------------------------------------------
# CFD operators and boundary conditions
