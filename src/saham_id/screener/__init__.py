"""Strategy screeners (intraday + swing).

Common entrypoints:
    from saham_id.screener.intraday import bpjs, bsjp, scalping
    from saham_id.screener.swing import breakout, pullback, reversal
"""

from saham_id.screener.engine import ScreenResult, ScreenRow

__all__ = ["ScreenResult", "ScreenRow"]
