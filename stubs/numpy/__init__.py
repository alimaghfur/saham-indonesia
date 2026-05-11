"""Minimal numpy stub for import/syntax testing."""
from __future__ import annotations
import math

# Constants
nan = float('nan')
inf = float('inf')
pi = math.pi
e = math.e


class ndarray:
    """Minimal ndarray stub."""
    def __init__(self, data=None):
        self._data = data or []


def array(obj, dtype=None):
    return ndarray(list(obj) if hasattr(obj, '__iter__') else [obj])


def isnan(x):
    if isinstance(x, (int, float)):
        return math.isnan(x)
    return False


def sign(x):
    """Element-wise sign. For Series compatibility."""
    if hasattr(x, 'apply'):
        def _sign(v):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return 0
            if v > 0:
                return 1
            elif v < 0:
                return -1
            return 0
        return x.apply(_sign)
    if isinstance(x, (int, float)):
        if x > 0:
            return 1
        elif x < 0:
            return -1
        return 0
    return x


def sqrt(x):
    if isinstance(x, (int, float)):
        return math.sqrt(x)
    return x


def log(x):
    if hasattr(x, 'apply'):
        import pandas as pd
        return x.apply(lambda v: math.log(v) if v > 0 else float('nan'))
    if isinstance(x, (int, float)):
        return math.log(x) if x > 0 else float('nan')
    return x


def mean(x):
    if hasattr(x, 'mean'):
        return x.mean()
    if hasattr(x, '__iter__'):
        data = list(x)
        return sum(data) / len(data) if data else 0.0
    return x


def std(x, ddof=0):
    if hasattr(x, 'std'):
        return x.std(ddof=ddof)
    return 0.0


def abs(x):
    import builtins
    if hasattr(x, 'abs'):
        return x.abs()
    return builtins.abs(x)
