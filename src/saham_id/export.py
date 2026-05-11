"""Export utilities — CSV, JSON, Excel output.

Usage:
    from saham_id.export import to_csv, to_json, to_excel

    result = breakout_screen(universe="LQ45")
    to_csv(result.to_dataframe(), "output/breakout.csv")
    to_json(result.to_dataframe(), "output/breakout.json")
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


def to_csv(
    df: pd.DataFrame,
    filepath: str | Path,
    index: bool = True,
) -> Path:
    """Export DataFrame to CSV file.

    Creates parent directories if needed.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use pandas to_csv if available, else manual
    if hasattr(df, 'to_csv'):
        df.to_csv(str(path), index=index)
    else:
        _manual_csv(df, path, index=index)

    return path


def to_json(
    df: pd.DataFrame,
    filepath: str | Path,
    orient: str = "records",
    indent: int = 2,
) -> Path:
    """Export DataFrame to JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(df, 'to_json'):
        df.to_json(str(path), orient=orient, indent=indent)
    else:
        _manual_json(df, path, indent=indent)

    return path


def to_excel(
    df: pd.DataFrame,
    filepath: str | Path,
    sheet_name: str = "Sheet1",
    index: bool = True,
) -> Path:
    """Export DataFrame to Excel file (.xlsx).

    Requires openpyxl: pip install openpyxl
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(df, 'to_excel'):
        df.to_excel(str(path), sheet_name=sheet_name, index=index)
    else:
        raise ImportError(
            "Excel export requires real pandas with openpyxl. "
            "Install with: pip install pandas openpyxl"
        )

    return path


def export_screen_result(
    result,
    filepath: str | Path,
    format: str = "csv",
) -> Path:
    """Export a ScreenResult to file.

    Automatically includes metadata (strategy, params, timestamp).
    """
    df = result.to_dataframe()
    path = Path(filepath)

    if format == "csv":
        return to_csv(df, path)
    elif format == "json":
        # Include metadata in JSON export
        data = {
            "strategy": result.strategy,
            "universe": result.universe,
            "as_of": result.as_of.isoformat() if result.as_of else None,
            "params": result.params,
            "total_results": len(result.rows),
            "data": _df_to_records(df),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        return path
    elif format == "excel":
        return to_excel(df, path)
    else:
        raise ValueError(f"Unknown format '{format}'. Use: csv, json, excel")


def export_backtest_result(
    result,
    metrics,
    filepath: str | Path,
    format: str = "json",
) -> Path:
    """Export backtest result with metrics to file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "summary": {
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
            "total_return": result.total_return,
            "total_return_pct": f"{result.total_return*100:.2f}%",
        },
        "metrics": {
            "cagr": metrics.cagr,
            "sharpe": metrics.sharpe,
            "sortino": metrics.sortino,
            "max_drawdown": metrics.max_drawdown,
            "win_rate": metrics.win_rate,
            "num_trades": metrics.num_trades,
            "avg_trade_pct": metrics.avg_trade_pct,
            "profit_factor": metrics.profit_factor,
        },
        "trades": [
            {
                "entry_time": str(t.entry_time),
                "exit_time": str(t.exit_time),
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "quantity": t.quantity,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
            }
            for t in result.trades
        ],
    }

    if format == "json":
        path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    elif format == "csv":
        # Export trades as CSV
        trades_df = pd.DataFrame(data["trades"])
        to_csv(trades_df, path, index=False)
    else:
        raise ValueError(f"Unknown format '{format}'. Use: json, csv")

    return path


def export_portfolio(
    portfolio,
    filepath: str | Path,
    format: str = "json",
    source: Optional[Any] = None,
) -> Path:
    """Export portfolio positions and transactions."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "cash": float(portfolio.cash),
        "positions": [
            {
                "ticker": pos.ticker,
                "quantity": pos.quantity,
                "avg_cost": float(pos.avg_cost),
                "realized_pnl": float(pos.realized_pnl),
            }
            for pos in portfolio.positions.values()
            if pos.quantity > 0
        ],
        "transactions": [
            {
                "timestamp": tx.timestamp.isoformat(),
                "ticker": tx.ticker,
                "side": tx.side,
                "quantity": tx.quantity,
                "price": float(tx.price),
                "fee": float(tx.fee),
                "note": tx.note,
            }
            for tx in portfolio.transactions
        ],
    }

    if format == "json":
        path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    elif format == "csv":
        tx_df = pd.DataFrame(data["transactions"])
        to_csv(tx_df, path, index=False)
    else:
        raise ValueError(f"Unknown format '{format}'. Use: json, csv")

    return path


# --- Internal helpers ---


def _df_to_records(df) -> list[dict]:
    """Convert DataFrame to list of dicts."""
    if hasattr(df, 'to_dict'):
        return df.to_dict(orient='records')
    # Manual for our stub DataFrame
    records = []
    if hasattr(df, '_data') and hasattr(df, 'columns'):
        n = len(df)
        for i in range(n):
            row = {}
            for col in df.columns:
                if col in df._data:
                    row[col] = df._data[col][i]
            records.append(row)
    return records


def _manual_csv(df, path: Path, index: bool = True) -> None:
    """Write DataFrame to CSV without real pandas."""
    with open(path, 'w') as f:
        cols = df.columns if hasattr(df, 'columns') else []
        if index:
            f.write("index," + ",".join(str(c) for c in cols) + "\n")
        else:
            f.write(",".join(str(c) for c in cols) + "\n")

        n = len(df) if hasattr(df, '__len__') else 0
        for i in range(n):
            row_vals = []
            if index:
                idx = df.index[i] if hasattr(df, 'index') and i < len(df.index) else i
                row_vals.append(str(idx))
            for col in cols:
                val = df._data.get(col, [])[i] if hasattr(df, '_data') else ""
                row_vals.append(str(val))
            f.write(",".join(row_vals) + "\n")


def _manual_json(df, path: Path, indent: int = 2) -> None:
    """Write DataFrame to JSON without real pandas."""
    records = _df_to_records(df)
    path.write_text(json.dumps(records, indent=indent, default=str, ensure_ascii=False))
