"""Bandarmology — analisis akumulasi/distribusi oleh smart money (bandar).

Deteksi apakah big player sedang akumulasi, distribusi, markup, atau markdown.
Menggunakan: Money Flow, ADL, Smart Money Index, dan Wyckoff phase detection.

Usage:
    from saham_id.analysis.bandarmology import bandar_score, bandar_scan
    result = bandar_score("BBCA", source=src)
    print(result.phase, result.score, result.interpretation)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import pandas as pd
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


class BandarPhase(str, Enum):
    ACCUMULATION = "ACCUMULATION"
    MARKUP = "MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    MARKDOWN = "MARKDOWN"
    NEUTRAL = "NEUTRAL"


PHASE_RECOMMENDATIONS = {
    BandarPhase.ACCUMULATION: "Pertimbangkan BELI bertahap — bandar kemungkinan sedang akumulasi",
    BandarPhase.MARKUP: "HOLD / trailing stop — bandar sedang mendorong harga naik",
    BandarPhase.DISTRIBUTION: "Waspada — bandar kemungkinan mulai distribusi",
    BandarPhase.MARKDOWN: "HINDARI / cut loss — bandar kemungkinan sudah keluar",
    BandarPhase.NEUTRAL: "Wait & see — belum ada indikasi kuat aktivitas bandar",
}


@dataclass
class MoneyFlowResult:
    net_flow_5d: float = 0.0
    net_flow_20d: float = 0.0
    flow_ratio: float = 0.0
    avg_buy_volume: float = 0.0
    avg_sell_volume: float = 0.0
    buy_sell_ratio: float = 0.0


@dataclass
class SmartMoneyResult:
    smart_money_index: float = 0.0
    large_transaction_pct: float = 0.0
    unusual_volume_days: int = 0
    stealth_accumulation: bool = False
    stealth_distribution: bool = False


@dataclass
class BandarScore:
    ticker: str
    phase: BandarPhase
    score: float
    confidence: float
    interpretation: str = ""
    recommendation: str = ""
    money_flow: Optional[MoneyFlowResult] = None
    smart_money: Optional[SmartMoneyResult] = None
    details: dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.interpretation:
            self.interpretation = PHASE_RECOMMENDATIONS.get(self.phase, "")
        if not self.recommendation:
            self.recommendation = PHASE_RECOMMENDATIONS.get(self.phase, "")


def money_flow(df: pd.DataFrame, short_window: int = 5, long_window: int = 20) -> MoneyFlowResult:
    if df.empty or len(df) < long_window:
        return MoneyFlowResult()
    flows, buy_vols, sell_vols = [], [], []
    for i in range(len(df)):
        o, h, l, c, v = df["open"].iloc[i], df["high"].iloc[i], df["low"].iloc[i], df["close"].iloc[i], df["volume"].iloc[i]
        if any(x is None for x in (o, h, l, c, v)):
            flows.append(0); continue
        o_f, h_f, l_f, c_f, v_f = float(o), float(h), float(l), float(c), float(v)
        rng = h_f - l_f
        if rng == 0:
            flows.append(0); continue
        mf = ((c_f - l_f) - (h_f - c_f)) / rng
        flows.append(mf * v_f * c_f)
        if c_f > o_f: buy_vols.append(v_f)
        elif c_f < o_f: sell_vols.append(v_f)
    net_5d = sum(flows[-short_window:])
    net_20d = sum(flows[-long_window:])
    total = sum(abs(f) for f in flows[-long_window:])
    pos = sum(f for f in flows[-long_window:] if f > 0)
    fr = pos / total if total > 0 else 0.5
    ab = sum(buy_vols[-long_window:]) / len(buy_vols[-long_window:]) if buy_vols else 0
    av = sum(sell_vols[-long_window:]) / len(sell_vols[-long_window:]) if sell_vols else 0
    return MoneyFlowResult(net_flow_5d=net_5d, net_flow_20d=net_20d, flow_ratio=fr,
                          avg_buy_volume=ab, avg_sell_volume=av, buy_sell_ratio=ab/av if av > 0 else 1.0)


def accumulation_distribution(close, high, low, volume) -> pd.Series:
    n = len(close)
    vals, cum = [], 0.0
    for i in range(n):
        c, h, l, v = close.iloc[i], high.iloc[i], low.iloc[i], volume.iloc[i]
        if any(x is None for x in (c, h, l, v)):
            vals.append(cum); continue
        rng = float(h) - float(l)
        if rng > 0:
            mf = ((float(c) - float(l)) - (float(h) - float(c))) / rng
            cum += mf * float(v)
        vals.append(cum)
    return pd.Series(vals)


def smart_money_index(df: pd.DataFrame, lookback: int = 20) -> SmartMoneyResult:
    if df.empty or len(df) < lookback:
        return SmartMoneyResult()
    recent = df.tail(lookback)
    volumes = [float(v) for v in recent["volume"] if v is not None]
    avg_vol = sum(volumes) / len(volumes) if volumes else 0
    unusual, stealth_buy, stealth_sell, large_sum = 0, 0, 0, 0.0
    for i in range(len(recent)):
        o, h, l, c, v = recent["open"].iloc[i], recent["high"].iloc[i], recent["low"].iloc[i], recent["close"].iloc[i], recent["volume"].iloc[i]
        if any(x is None for x in (o, h, l, c, v)): continue
        o_f, h_f, l_f, c_f, v_f = float(o), float(h), float(l), float(c), float(v)
        rng = h_f - l_f
        if avg_vol > 0 and v_f > avg_vol * 2:
            unusual += 1; large_sum += v_f
        if avg_vol > 0 and v_f > avg_vol * 1.5 and rng > 0:
            if abs(c_f - o_f) / rng < 0.3:
                mid = (h_f + l_f) / 2
                if c_f > mid: stealth_buy += 1
                elif c_f < mid: stealth_sell += 1
    smi = 50.0
    if avg_vol > 0 and len(volumes) >= 5:
        smi += ((sum(volumes[-5:]) / 5) / avg_vol - 1.0) * 20
    smi += stealth_buy * 5 - stealth_sell * 5 + unusual * 3
    smi = max(0, min(100, smi))
    return SmartMoneyResult(smart_money_index=round(smi, 1), large_transaction_pct=round(large_sum/sum(volumes), 3) if volumes else 0,
                           unusual_volume_days=unusual, stealth_accumulation=stealth_buy >= 3, stealth_distribution=stealth_sell >= 3)


def detect_phase(df: pd.DataFrame, lookback: int = 30) -> BandarPhase:
    if df.empty or len(df) < lookback:
        return BandarPhase.NEUTRAL
    recent = df.tail(lookback)
    close = recent["close"]
    mid = len(recent) // 2
    f_avg = sum(float(close.iloc[i]) for i in range(mid) if close.iloc[i] is not None) / max(mid, 1)
    s_avg = sum(float(close.iloc[i]) for i in range(mid, len(recent)) if close.iloc[i] is not None) / max(len(recent)-mid, 1)
    if f_avg == 0: return BandarPhase.NEUTRAL
    price_trend = (s_avg - f_avg) / f_avg
    volumes = [float(recent["volume"].iloc[i]) for i in range(len(recent)) if recent["volume"].iloc[i] is not None]
    if len(volumes) < 10: return BandarPhase.NEUTRAL
    fv = sum(volumes[:mid]) / max(mid, 1)
    sv = sum(volumes[mid:]) / max(len(volumes)-mid, 1)
    vol_trend = (sv - fv) / fv if fv > 0 else 0
    adl = accumulation_distribution(recent["close"], recent["high"], recent["low"], recent["volume"])
    adl_trend = 1 if adl.iloc[-1] > adl.iloc[0] else (-1 if adl.iloc[-1] < adl.iloc[0] else 0)
    sideways = abs(price_trend) < 0.03
    up = price_trend > 0.05
    down = price_trend < -0.05
    vol_inc = vol_trend > 0.2
    if sideways and vol_inc and adl_trend > 0: return BandarPhase.ACCUMULATION
    if up and adl_trend > 0: return BandarPhase.MARKUP
    if sideways and vol_inc and adl_trend < 0: return BandarPhase.DISTRIBUTION
    if down and adl_trend < 0: return BandarPhase.MARKDOWN
    return BandarPhase.NEUTRAL


def bandar_score(ticker: str, period: str = "6mo", lookback: int = 30, source: Optional[DataSource] = None) -> BandarScore:
    src = source or get_source()
    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception:
        return BandarScore(ticker=ticker, phase=BandarPhase.NEUTRAL, score=50, confidence=0)
    if df.empty or len(df) < lookback:
        return BandarScore(ticker=ticker, phase=BandarPhase.NEUTRAL, score=50, confidence=0)
    mf = money_flow(df)
    smi = smart_money_index(df, lookback=lookback)
    phase = detect_phase(df, lookback=lookback)
    score = 50.0
    score += (mf.flow_ratio - 0.5) * 40
    if mf.buy_sell_ratio > 1.3: score += min(15, (mf.buy_sell_ratio - 1.0) * 10)
    elif mf.buy_sell_ratio < 0.7: score -= min(15, (1.0 - mf.buy_sell_ratio) * 10)
    score += (smi.smart_money_index - 50) * 0.3
    bonus = {BandarPhase.ACCUMULATION: 15, BandarPhase.MARKUP: 10, BandarPhase.DISTRIBUTION: -15, BandarPhase.MARKDOWN: -20, BandarPhase.NEUTRAL: 0}
    score += bonus.get(phase, 0)
    if smi.stealth_accumulation: score += 10
    if smi.stealth_distribution: score -= 10
    score = max(0, min(100, score))
    confidence = min(1.0, (abs(score - 50) / 50) * 1.5)
    if score >= 70: interp = "Indikasi KUAT akumulasi bandar"
    elif score >= 60: interp = "Indikasi MODERAT akumulasi"
    elif score >= 40: interp = "NETRAL — belum ada indikasi kuat"
    elif score >= 30: interp = "Indikasi MODERAT distribusi"
    else: interp = "Indikasi KUAT distribusi"
    return BandarScore(ticker=ticker, phase=phase, score=round(score, 1), confidence=round(confidence, 2),
                      interpretation=interp, money_flow=mf, smart_money=smi, details={"flow_ratio": mf.flow_ratio, "buy_sell_ratio": mf.buy_sell_ratio, "smi": smi.smart_money_index})


def bandar_scan(universe: str = "LQ45", min_score: float = 60.0, top_n: int = 15, source: Optional[DataSource] = None) -> list[BandarScore]:
    from saham_id.data.universe import get_universe
    src = source or get_source()
    results = []
    for ticker in get_universe(universe):
        try:
            bs = bandar_score(ticker, source=src)
            if bs.score >= min_score: results.append(bs)
        except Exception: continue
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]
