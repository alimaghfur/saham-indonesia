"""Minimal yfinance stub for import testing."""


class Ticker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.fast_info = {}
        self.info = {}


class Tickers:
    def __init__(self, symbols):
        self.tickers = {}


def download(tickers, period=None, interval=None, progress=False, auto_adjust=False, threads=False):
    import pandas as pd
    return pd.DataFrame()
