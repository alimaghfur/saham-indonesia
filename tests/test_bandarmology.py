"""Tests for bandarmology module."""
import pandas as pd
import math
from saham_id.analysis.bandarmology import (
    BandarPhase, BandarScore, MoneyFlowResult, SmartMoneyResult,
    bandar_score, detect_phase, money_flow, smart_money_index,
    accumulation_distribution, bandar_scan, PHASE_RECOMMENDATIONS,
)


def _markup_data(n=60):
    """Markup: close near high (strong buying), trending up."""
    close = [1000 + i * 10 for i in range(n)]
    return pd.DataFrame({"open": [c-8 for c in close], "high": [c+2 for c in close],
                        "low": [c-10 for c in close], "close": close, "volume": [2000000+i*20000 for i in range(n)]})

def _markdown_data(n=60):
    """Markdown: close near low (strong selling), trending down."""
    close = [2000 - i * 10 for i in range(n)]
    return pd.DataFrame({"open": [c+8 for c in close], "high": [c+10 for c in close],
                        "low": [c-2 for c in close], "close": close, "volume": [1500000+i*5000 for i in range(n)]})


class TestBandarPhase:
    def test_all_phases_have_recommendations(self):
        for phase in BandarPhase:
            assert phase in PHASE_RECOMMENDATIONS

class TestMoneyFlow:
    def test_positive_flow(self):
        df = _markup_data(40)
        result = money_flow(df)
        assert result.net_flow_20d > 0
        assert result.flow_ratio > 0.5
        assert result.buy_sell_ratio >= 1.0

    def test_negative_flow(self):
        df = _markdown_data(40)
        result = money_flow(df)
        assert result.net_flow_20d < 0

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert money_flow(df).net_flow_5d == 0.0

class TestADL:
    def test_rising(self):
        df = _markup_data(30)
        adl = accumulation_distribution(df["close"], df["high"], df["low"], df["volume"])
        assert adl.iloc[-1] > adl.iloc[0]

    def test_falling(self):
        df = _markdown_data(30)
        adl = accumulation_distribution(df["close"], df["high"], df["low"], df["volume"])
        assert adl.iloc[-1] < adl.iloc[0]

class TestSmartMoney:
    def test_basic(self):
        df = _markup_data(30)
        result = smart_money_index(df, lookback=20)
        assert 0 <= result.smart_money_index <= 100

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert smart_money_index(df).smart_money_index == 0.0

class TestDetectPhase:
    def test_markup(self):
        assert detect_phase(_markup_data(60), lookback=30) == BandarPhase.MARKUP

    def test_markdown(self):
        assert detect_phase(_markdown_data(60), lookback=30) == BandarPhase.MARKDOWN

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert detect_phase(df) == BandarPhase.NEUTRAL

class TestBandarScore:
    def test_create(self):
        bs = BandarScore(ticker="BBCA", phase=BandarPhase.ACCUMULATION, score=75, confidence=0.8)
        assert bs.ticker == "BBCA"
        assert bs.recommendation != ""

    def test_nonexistent(self):
        bs = bandar_score("ZZZZNONEXIST")
        assert bs.phase == BandarPhase.NEUTRAL
        assert bs.confidence == 0
