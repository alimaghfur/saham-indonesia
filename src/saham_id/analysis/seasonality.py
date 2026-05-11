"""Seasonality analysis — detect calendar effects in IDX stocks.

Analyzes historical patterns by:
    - Month-of-year (e.g. "Sell in May" effect)
    - Day-of-week (Monday effect, Friday rally)
    - Pre/post-holiday effects

Usage:
    from saham_id.analysis.seasonality import monthly_seasonality, day_of_week_effect

    monthly = monthly_seasonality("BBCA", source=src)
    print(monthly.best_month)   # "December"
    print(monthly.worst_month)  # "May"

    dow = day_of_week_effect("BBCA", source=src)
    print(dow.best_day)   # "Friday"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


@dataclass
class MonthlySeasonality:
    """Monthly return statistics."""

    ticker: str
    period: str
    monthly_returns: dict[str, float] = field(default_factory=dict)  # month_name -> avg return
    monthly_win_rates: dict[str, float] = field(default_factory=dict)  # month_name -> win rate
    monthly_counts: dict[str, int] = field(default_factory=dict)  # month_name -> sample count

    @property
    def best_month(self) -> str:
        if not self.monthly_returns:
            return ""
        return max(self.monthly_returns.items(), key=lambda x: x[1])[0]

    @property
    def worst_month(self) -> str:
        if not self.monthly_returns:
            return ""
        return min(self.monthly_returns.items(), key=lambda x: x[1])[0]

    def to_dataframe(self):
        import pandas as pd
        rows = []
        for month in MONTH_NAMES:
            rows.append({
                "month": month,
                "avg_return": self.monthly_returns.get(month, 0.0),
                "win_rate": self.monthly_win_rates.get(month, 0.0),
                "samples": self.monthly_counts.get(month, 0),
            })
        return pd.DataFrame(rows)


@dataclass
class DayOfWeekEffect:
    """Day-of-week return statistics."""

    ticker: str
    period: str
    daily_returns: dict[str, float] = field(default_factory=dict)  # day_name -> avg return
    daily_win_rates: dict[str, float] = field(default_factory=dict)
    daily_counts: dict[str, int] = field(default_factory=dict)

    @property
    def best_day(self) -> str:
        if not self.daily_returns:
            return ""
        return max(self.daily_returns.items(), key=lambda x: x[1])[0]

    @property
    def worst_day(self) -> str:
        if not self.daily_returns:
            return ""
        return min(self.daily_returns.items(), key=lambda x: x[1])[0]

    def to_dataframe(self):
        import pandas as pd
        rows = []
        for day in DAY_NAMES:
            rows.append({
                "day": day,
                "avg_return": self.daily_returns.get(day, 0.0),
                "win_rate": self.daily_win_rates.get(day, 0.0),
                "samples": self.daily_counts.get(day, 0),
            })
        return pd.DataFrame(rows)


def monthly_seasonality(
    ticker: str,
    period: str = "5y",
    source: Optional[DataSource] = None,
) -> MonthlySeasonality:
    """Analyze monthly return patterns over historical data.

    Computes average return and win rate for each calendar month.
    """
    src = source or get_source()

    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception:
        return MonthlySeasonality(ticker=ticker, period=period)

    if df.empty or len(df) < 60:
        return MonthlySeasonality(ticker=ticker, period=period)

    # Compute daily returns
    close = df["close"]
    returns_data = close.pct_change()

    # Group by month
    month_returns: dict[int, list[float]] = {m: [] for m in range(1, 13)}

    index = df.index if hasattr(df, 'index') else list(range(len(df)))
    for i in range(1, len(df)):
        ret = returns_data.iloc[i]
        if ret is None:
            continue

        # Get month from index
        idx = index[i] if isinstance(index, list) else df.index[i]
        if hasattr(idx, 'month'):
            month = idx.month
        elif hasattr(idx, 'timetuple'):
            month = idx.timetuple().tm_mon
        else:
            continue

        month_returns[month].append(float(ret))

    # Compute statistics
    monthly_avg: dict[str, float] = {}
    monthly_wr: dict[str, float] = {}
    monthly_cnt: dict[str, int] = {}

    for month_num, rets in month_returns.items():
        if not rets:
            continue
        month_name = MONTH_NAMES[month_num - 1]
        monthly_avg[month_name] = sum(rets) / len(rets)
        monthly_wr[month_name] = sum(1 for r in rets if r > 0) / len(rets)
        monthly_cnt[month_name] = len(rets)

    return MonthlySeasonality(
        ticker=ticker,
        period=period,
        monthly_returns=monthly_avg,
        monthly_win_rates=monthly_wr,
        monthly_counts=monthly_cnt,
    )


def day_of_week_effect(
    ticker: str,
    period: str = "5y",
    source: Optional[DataSource] = None,
) -> DayOfWeekEffect:
    """Analyze day-of-week return patterns.

    Checks for Monday effect, Friday rally, etc.
    """
    src = source or get_source()

    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception:
        return DayOfWeekEffect(ticker=ticker, period=period)

    if df.empty or len(df) < 60:
        return DayOfWeekEffect(ticker=ticker, period=period)

    close = df["close"]
    returns_data = close.pct_change()

    # Group by day of week
    dow_returns: dict[int, list[float]] = {d: [] for d in range(5)}

    index = df.index if hasattr(df, 'index') else list(range(len(df)))
    for i in range(1, len(df)):
        ret = returns_data.iloc[i]
        if ret is None:
            continue

        idx = index[i] if isinstance(index, list) else df.index[i]
        if hasattr(idx, 'weekday'):
            dow = idx.weekday() if callable(idx.weekday) else idx.weekday
        elif hasattr(idx, 'timetuple'):
            dow = idx.timetuple().tm_wday
        else:
            continue

        if 0 <= dow <= 4:
            dow_returns[dow].append(float(ret))

    # Compute statistics
    daily_avg: dict[str, float] = {}
    daily_wr: dict[str, float] = {}
    daily_cnt: dict[str, int] = {}

    for dow_num, rets in dow_returns.items():
        if not rets:
            continue
        day_name = DAY_NAMES[dow_num]
        daily_avg[day_name] = sum(rets) / len(rets)
        daily_wr[day_name] = sum(1 for r in rets if r > 0) / len(rets)
        daily_cnt[day_name] = len(rets)

    return DayOfWeekEffect(
        ticker=ticker,
        period=period,
        daily_returns=daily_avg,
        daily_win_rates=daily_wr,
        daily_counts=daily_cnt,
    )


def sell_in_may_effect(
    ticker: str,
    period: str = "10y",
    source: Optional[DataSource] = None,
) -> dict:
    """Analyze 'Sell in May' effect (May-October vs November-April).

    Returns dict with:
        - may_oct_return: average daily return May-Oct
        - nov_apr_return: average daily return Nov-Apr
        - effect_exists: bool (is May-Oct significantly worse?)
    """
    src = source or get_source()
    seasonality = monthly_seasonality(ticker, period=period, source=src)

    if not seasonality.monthly_returns:
        return {"may_oct_return": 0.0, "nov_apr_return": 0.0, "effect_exists": False}

    summer_months = ["May", "June", "July", "August", "September", "October"]
    winter_months = ["November", "December", "January", "February", "March", "April"]

    summer_rets = [seasonality.monthly_returns.get(m, 0.0) for m in summer_months if m in seasonality.monthly_returns]
    winter_rets = [seasonality.monthly_returns.get(m, 0.0) for m in winter_months if m in seasonality.monthly_returns]

    summer_avg = sum(summer_rets) / len(summer_rets) if summer_rets else 0.0
    winter_avg = sum(winter_rets) / len(winter_rets) if winter_rets else 0.0

    return {
        "may_oct_return": summer_avg,
        "nov_apr_return": winter_avg,
        "effect_exists": winter_avg > summer_avg * 1.5,
        "summer_months": {m: seasonality.monthly_returns.get(m, 0) for m in summer_months},
        "winter_months": {m: seasonality.monthly_returns.get(m, 0) for m in winter_months},
    }
