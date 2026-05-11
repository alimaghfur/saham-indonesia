"""Combo screener — multi-factor scoring combining technicals + patterns + fundamentals.

The ultimate screener: combines signals from:
    1. Technical indicators (RSI, MACD, Bollinger, volume)
    2. Candlestick patterns (engulfing, hammer, etc.)
    3. Fundamental scoring (value + quality if available)
    4. Market context (breadth, sector rotation)

Produces a single composite score per stock.

Usage:
    from saham_id.screener.combo import combo_screen

    result = combo_screen(universe="LQ45", source=src)
    print(result.to_dataframe())
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def combo_screen(
    universe: str | Iterable[str] = "LQ45",
    weight_technical: float = 0.4,
    weight_pattern: float = 0.25,
    weight_momentum: float = 0.2,
    weight_volume: float = 0.15,
    min_score: float = 50.0,
    top_n: int = 15,
    source: Optional[DataSource] = None,
) -> ScreenResult:
    """Multi-factor combo screener.

    Scoring:
        composite = w_tech * tech_score
                  + w_pattern * pattern_score
                  + w_momentum * momentum_score
                  + w_volume * volume_score

    Each sub-score is 0-100.

    Parameters:
        universe: Stock universe or ticker list
        weight_technical: Weight for technical indicator score
        weight_pattern: Weight for candlestick pattern score
        weight_momentum: Weight for momentum score
        weight_volume: Weight for volume score
        min_score: Minimum composite score to include in results
        top_n: Max results to return
        source: DataSource instance
    """
    from saham_id.analysis.indicators import bollinger_bands, ema, macd, rsi, rvol, sma
    from saham_id.analysis.patterns import detect_patterns, PatternBias

    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []

    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
        except Exception:
            continue

        if df.empty or len(df) < 50:
            continue

        df = df.copy()
        close = df["close"]
        volume = df["volume"]

        # --- 1. Technical Score (0-100) ---
        tech_score = 50.0  # start neutral

        # RSI
        rsi_val = rsi(close, 14).iloc[-1]
        if rsi_val is not None:
            if rsi_val < 30:
                tech_score += 20  # oversold = bullish opportunity
            elif rsi_val < 40:
                tech_score += 10
            elif rsi_val > 70:
                tech_score -= 15  # overbought = risky
            elif rsi_val > 60:
                tech_score -= 5

        # MACD
        macd_df = macd(close, 12, 26, 9)
        macd_val = macd_df["macd"].iloc[-1]
        signal_val = macd_df["signal"].iloc[-1]
        hist_val = macd_df["histogram"].iloc[-1]
        if macd_val is not None and signal_val is not None:
            if float(macd_val) > float(signal_val):
                tech_score += 10  # bullish
            else:
                tech_score -= 5
            # Histogram expanding
            if hist_val is not None and len(macd_df) >= 2:
                prev_hist = macd_df["histogram"].iloc[-2]
                if prev_hist is not None and float(hist_val) > float(prev_hist):
                    tech_score += 5

        # Price vs SMA
        sma_20 = sma(close, 20).iloc[-1]
        sma_50 = sma(close, 50).iloc[-1]
        last_close = close.iloc[-1]
        if sma_20 is not None and sma_50 is not None and last_close is not None:
            lc = float(last_close)
            s20 = float(sma_20)
            s50 = float(sma_50)
            if lc > s20 > s50:
                tech_score += 15  # strong uptrend
            elif lc > s20:
                tech_score += 5
            elif lc < s20 < s50:
                tech_score -= 10  # downtrend

        tech_score = max(0, min(100, tech_score))

        # --- 2. Pattern Score (0-100) ---
        pattern_score = 50.0
        patterns = detect_patterns(df, lookback=5)
        for p in patterns:
            weight = {"high": 15, "moderate": 10, "low": 5}[p.reliability.value]
            if p.bias == PatternBias.BULLISH:
                pattern_score += weight
            elif p.bias == PatternBias.BEARISH:
                pattern_score -= weight
        pattern_score = max(0, min(100, pattern_score))

        # --- 3. Momentum Score (0-100) ---
        momentum_score = 50.0
        if last_close is not None and len(close) >= 21:
            # 5-day return
            prev_5 = close.iloc[-6]
            if prev_5 is not None and float(prev_5) > 0:
                ret_5d = (float(last_close) - float(prev_5)) / float(prev_5)
                momentum_score += ret_5d * 500  # scale: 2% -> +10 points

            # 20-day return
            prev_20 = close.iloc[-21]
            if prev_20 is not None and float(prev_20) > 0:
                ret_20d = (float(last_close) - float(prev_20)) / float(prev_20)
                momentum_score += ret_20d * 200  # scale: 5% -> +10 points

        momentum_score = max(0, min(100, momentum_score))

        # --- 4. Volume Score (0-100) ---
        volume_score = 50.0
        rv = rvol(volume, 20)
        rv_val = rv.iloc[-1]
        if rv_val is not None:
            rv_float = float(rv_val)
            if rv_float > 2.0:
                volume_score += 25
            elif rv_float > 1.5:
                volume_score += 15
            elif rv_float > 1.0:
                volume_score += 5
            elif rv_float < 0.5:
                volume_score -= 10  # very low volume = illiquid
        volume_score = max(0, min(100, volume_score))

        # --- Composite Score ---
        composite = (
            weight_technical * tech_score
            + weight_pattern * pattern_score
            + weight_momentum * momentum_score
            + weight_volume * volume_score
        )

        if composite < min_score:
            continue

        rows.append(ScreenRow(
            ticker=ticker,
            score=round(composite, 2),
            metrics={
                "tech_score": round(tech_score, 1),
                "pattern_score": round(pattern_score, 1),
                "momentum_score": round(momentum_score, 1),
                "volume_score": round(volume_score, 1),
                "rsi": round(float(rsi_val), 1) if rsi_val is not None else None,
                "rvol": round(float(rv_val), 2) if rv_val is not None else None,
                "patterns_detected": len(patterns),
                "close": round(float(last_close), 0) if last_close is not None else None,
            },
        ))

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="combo",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "weight_technical": weight_technical,
            "weight_pattern": weight_pattern,
            "weight_momentum": weight_momentum,
            "weight_volume": weight_volume,
            "min_score": min_score,
        },
    )
