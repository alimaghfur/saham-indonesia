"""Ichimoku Cloud indicator."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


@dataclass
class IchimokuResult:
    tenkan: pd.Series
    kijun: pd.Series
    senkou_a: pd.Series
    senkou_b: pd.Series
    chikou: pd.Series
    cloud_color: str = ""
    price_vs_cloud: str = ""
    tk_cross: str = ""


def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series,
             tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52) -> IchimokuResult:
    h_data = high._data if hasattr(high, '_data') else list(high)
    l_data = low._data if hasattr(low, '_data') else list(low)
    c_data = close._data if hasattr(close, '_data') else list(close)
    n = len(h_data)

    tenkan_vals, kijun_vals = [], []
    for i in range(n):
        start_t = max(0, i - tenkan_period + 1)
        h_win = [v for v in h_data[start_t:i+1] if v is not None]
        l_win = [v for v in l_data[start_t:i+1] if v is not None]
        tenkan_vals.append((max(h_win) + min(l_win)) / 2 if len(h_win) >= tenkan_period else None)
        start_k = max(0, i - kijun_period + 1)
        h_win_k = [v for v in h_data[start_k:i+1] if v is not None]
        l_win_k = [v for v in l_data[start_k:i+1] if v is not None]
        kijun_vals.append((max(h_win_k) + min(l_win_k)) / 2 if len(h_win_k) >= kijun_period else None)

    senkou_a_vals = [(t + k) / 2 if t is not None and k is not None else None for t, k in zip(tenkan_vals, kijun_vals)]
    senkou_b_vals = []
    for i in range(n):
        start_sb = max(0, i - senkou_b_period + 1)
        h_win_sb = [v for v in h_data[start_sb:i+1] if v is not None]
        l_win_sb = [v for v in l_data[start_sb:i+1] if v is not None]
        senkou_b_vals.append((max(h_win_sb) + min(l_win_sb)) / 2 if len(h_win_sb) >= senkou_b_period else None)

    chikou_vals = c_data[kijun_period:] + [None] * min(kijun_period, n)

    last_sa = senkou_a_vals[-1] if senkou_a_vals and senkou_a_vals[-1] is not None else 0
    last_sb = senkou_b_vals[-1] if senkou_b_vals and senkou_b_vals[-1] is not None else 0
    last_close = c_data[-1] if c_data else 0
    last_t = tenkan_vals[-1] if tenkan_vals and tenkan_vals[-1] is not None else 0
    last_k = kijun_vals[-1] if kijun_vals and kijun_vals[-1] is not None else 0

    cloud_color = "green" if last_sa > last_sb else "red"
    if last_close and last_sa and last_sb:
        cloud_top = max(float(last_sa), float(last_sb))
        cloud_bot = min(float(last_sa), float(last_sb))
        price_vs_cloud = "above" if float(last_close) > cloud_top else ("below" if float(last_close) < cloud_bot else "inside")
    else:
        price_vs_cloud = "unknown"
    tk_cross = "bullish" if last_t and last_k and float(last_t) > float(last_k) else "bearish"

    return IchimokuResult(tenkan=pd.Series(tenkan_vals), kijun=pd.Series(kijun_vals),
                         senkou_a=pd.Series(senkou_a_vals[:n]), senkou_b=pd.Series(senkou_b_vals[:n]),
                         chikou=pd.Series(chikou_vals[:n]), cloud_color=cloud_color,
                         price_vs_cloud=price_vs_cloud, tk_cross=tk_cross)
