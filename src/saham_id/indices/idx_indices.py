"""IDX index price history via yfinance.

Yahoo tickers for IDX indices:
    IHSG       -> ^JKSE
    LQ45       -> ^JKLQ45
    IDX30      -> (not widely available — may need alternative source)
    JII        -> ^JKII
"""

from __future__ import annotations

import pandas as pd

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource, Interval, Period, SourceError

IDX_INDEX_TICKERS: dict[str, str] = {
    "IHSG": "^JKSE",
    "LQ45": "^JKLQ45",
    "JII": "^JKII",
}


def get_index_history(
    name: str,
    period: Period = "1y",
    interval: Interval = "1d",
    source: DataSource | None = None,
) -> pd.DataFrame:
    """Return OHLC history for an IDX index by name (e.g. 'IHSG')."""
    key = name.upper()
    if key not in IDX_INDEX_TICKERS:
        available = ", ".join(IDX_INDEX_TICKERS)
        raise ValueError(f"Unknown index '{name}'. Available: {available}")
    src = source or get_source()
    try:
        return src.get_ohlc(IDX_INDEX_TICKERS[key], period=period, interval=interval)
    except SourceError as exc:
        raise SourceError(f"Failed to fetch index {key}: {exc}") from exc
