"""Reference strategies that plug into the `Backtester`.

Each module exposes a `strategy` callable compatible with
`Backtester(strategy=...)`.
"""

from saham_id.backtest.strategies.bpjs_strategy import bpjs_strategy
from saham_id.backtest.strategies.swing_pullback import swing_pullback_strategy

__all__ = ["bpjs_strategy", "swing_pullback_strategy"]
