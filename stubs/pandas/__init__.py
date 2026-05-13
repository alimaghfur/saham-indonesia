"""Minimal pandas stub for import/syntax testing.

This provides enough functionality to run unit tests for the saham-indonesia
project without requiring a real pandas installation.
"""
from __future__ import annotations
import math
from typing import Any, Optional

NA = None


def isna(x):
    if x is None:
        return True
    if isinstance(x, float) and math.isnan(x):
        return True
    return False


def notna(x):
    return not isna(x)


class Series:
    """Minimal Series stub with actual computation."""
    def __init__(self, data=None, index=None, name=None, dtype=None):
        if data is None:
            data = []
        if isinstance(data, Series):
            data = list(data._data)
            if index is None and data:
                index = data  # just use range
        if isinstance(data, dict):
            self._data = list(data.values())
            self._index = list(data.keys()) if index is None else list(index)
        elif isinstance(data, (list, tuple)):
            self._data = list(data)
            self._index = list(index) if index else list(range(len(self._data)))
        else:
            self._data = [data]
            self._index = list(index) if index else [0]
        self.name = name
        self.index = self._index
        self.values = self._data

    @property
    def iloc(self):
        return _ILoc(self)

    @property
    def empty(self):
        return len(self._data) == 0

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __bool__(self):
        if len(self._data) == 1:
            return bool(self._data[0])
        raise ValueError("Truth value of a Series is ambiguous")

    def __float__(self):
        if len(self._data) == 1:
            return float(self._data[0])
        raise TypeError("cannot convert Series to float")

    def __int__(self):
        if len(self._data) == 1:
            return int(self._data[0])
        raise TypeError("cannot convert Series to int")

    def __getitem__(self, key):
        if isinstance(key, str):
            # dict-like access for row (when Series acts as a row)
            if key in self._index:
                idx = self._index.index(key)
                return self._data[idx]
            return None
        if isinstance(key, int):
            return self._data[key]
        if isinstance(key, slice):
            sliced_data = self._data[key]
            sliced_index = self._index[key]
            return Series(sliced_data, sliced_index, self.name)
        # Boolean mask
        if isinstance(key, Series):
            result = [d for d, m in zip(self._data, key._data) if m]
            return Series(result)
        return self

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._data[key] = value
        elif isinstance(key, str):
            if key in self._index:
                idx = self._index.index(key)
                self._data[idx] = value

    def get(self, key, default=None):
        if isinstance(key, str) and key in self._index:
            idx = self._index.index(key)
            return self._data[idx]
        return default

    def _binop(self, other, op):
        if isinstance(other, Series):
            result = []
            for a, b in zip(self._data, other._data):
                if a is None or b is None or (isinstance(a, float) and math.isnan(a)) or (isinstance(b, float) and math.isnan(b)):
                    result.append(float('nan'))
                else:
                    result.append(op(a, b))
            return Series(result, list(self._index), self.name)
        else:
            result = []
            for a in self._data:
                if a is None or (isinstance(a, float) and math.isnan(a)):
                    result.append(float('nan'))
                else:
                    result.append(op(a, other))
            return Series(result, list(self._index), self.name)

    def _cmpop(self, other, op):
        def _safe_cmp(a, b):
            if a is None or b is None:
                return False
            if isinstance(a, float) and math.isnan(a):
                return False
            if isinstance(b, float) and math.isnan(b):
                return False
            return op(a, b)
        if isinstance(other, Series):
            return Series([_safe_cmp(a, b) for a, b in zip(self._data, other._data)], list(self._index))
        return Series([_safe_cmp(a, other) for a in self._data], list(self._index))

    def __truediv__(self, other): return self._binop(other, lambda a, b: a / b if b != 0 else float('nan'))
    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return Series([other / a if a != 0 else float('nan') for a in self._data], list(self._index))
        return NotImplemented
    def __mul__(self, other): return self._binop(other, lambda a, b: a * b)
    def __rmul__(self, other): return self.__mul__(other)
    def __sub__(self, other): return self._binop(other, lambda a, b: a - b)
    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return Series([other - a for a in self._data], list(self._index))
        return NotImplemented
    def __add__(self, other): return self._binop(other, lambda a, b: a + b)
    def __radd__(self, other): return self.__add__(other)
    def __neg__(self): return Series([-a if a is not None else None for a in self._data], list(self._index))
    def __pow__(self, other): return self._binop(other, lambda a, b: a ** b)

    def __gt__(self, other): return self._cmpop(other, lambda a, b: a > b)
    def __lt__(self, other): return self._cmpop(other, lambda a, b: a < b)
    def __ge__(self, other): return self._cmpop(other, lambda a, b: a >= b)
    def __le__(self, other): return self._cmpop(other, lambda a, b: a <= b)
    def __eq__(self, other): return self._cmpop(other, lambda a, b: a == b)
    def __ne__(self, other): return self._cmpop(other, lambda a, b: a != b)

    def __abs__(self):
        return self.abs()

    def abs(self):
        return Series([abs(a) if a is not None else None for a in self._data], list(self._index))

    def diff(self, periods=1):
        result = [None] * periods + [
            self._data[i] - self._data[i - periods]
            if self._data[i] is not None and self._data[i - periods] is not None
            else None
            for i in range(periods, len(self._data))
        ]
        return Series(result, list(self._index), self.name)

    def shift(self, periods=1):
        if periods > 0:
            result = [None] * periods + self._data[:-periods] if periods < len(self._data) else [None] * len(self._data)
        elif periods < 0:
            result = self._data[-periods:] + [None] * (-periods)
        else:
            result = list(self._data)
        return Series(result, list(self._index), self.name)

    def clip(self, lower=None, upper=None):
        result = []
        for v in self._data:
            if v is None:
                result.append(None)
            else:
                val = v
                if lower is not None:
                    val = max(val, lower)
                if upper is not None:
                    val = min(val, upper)
                result.append(val)
        return Series(result, list(self._index), self.name)

    def fillna(self, value=0):
        result = [value if (v is None or (isinstance(v, float) and math.isnan(v))) else v for v in self._data]
        return Series(result, list(self._index), self.name)

    def dropna(self):
        pairs = [(i, d) for i, d in zip(self._index, self._data)
                 if d is not None and not (isinstance(d, float) and math.isnan(d))]
        if not pairs:
            return Series([], [], self.name)
        idx, data = zip(*pairs)
        return Series(list(data), list(idx), self.name)

    def cumsum(self):
        result = []
        total = 0
        for v in self._data:
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                total += v
            result.append(total)
        return Series(result, list(self._index), self.name)

    def cummax(self):
        result = []
        mx = float('-inf')
        for v in self._data:
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                mx = max(mx, v)
            result.append(mx)
        return Series(result, list(self._index), self.name)

    def rolling(self, window=1, min_periods=None):
        return _Rolling(self, window, min_periods or window)

    def ewm(self, span=None, alpha=None, min_periods=None, adjust=True):
        return _EWM(self, span=span, alpha=alpha, min_periods=min_periods, adjust=adjust)

    def pct_change(self, periods=1):
        result = [None] * periods
        for i in range(periods, len(self._data)):
            prev = self._data[i - periods]
            cur = self._data[i]
            if prev and prev != 0 and cur is not None:
                result.append((cur - prev) / prev)
            else:
                result.append(None)
        return Series(result, list(self._index), self.name)

    def mean(self):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return sum(vals) / len(vals) if vals else 0.0

    def std(self, ddof=0):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        var = sum((x - m) ** 2 for x in vals) / (len(vals) - ddof)
        return math.sqrt(var)

    def var(self, ddof=0):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        return sum((x - m) ** 2 for x in vals) / (len(vals) - ddof)

    def min(self):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return min(vals) if vals else 0

    def max(self):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return max(vals) if vals else 0

    def sum(self):
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return sum(vals)

    def replace(self, to_replace, value=None):
        result = [value if v == to_replace else v for v in self._data]
        return Series(result, list(self._index), self.name)

    def apply(self, func):
        return Series([func(v) for v in self._data], list(self._index), self.name)

    def tail(self, n=5):
        return Series(self._data[-n:], self._index[-n:], self.name)

    def head(self, n=5):
        return Series(self._data[:n], self._index[:n], self.name)

    def quantile(self, q):
        vals = sorted([v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))])
        if not vals:
            return 0.0
        idx = int(q * (len(vals) - 1))
        return vals[idx]

    def copy(self):
        return Series(list(self._data), list(self._index), self.name)

    def where(self, cond, other=0):
        """Return elements where cond is True, else other."""
        if isinstance(cond, Series):
            result = [a if c else other for a, c in zip(self._data, cond._data)]
        else:
            result = [a if cond else other for a in self._data]
        return Series(result, list(self._index), self.name)

    def cumprod(self):
        """Cumulative product."""
        result = []
        prod = 1.0
        for v in self._data:
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                prod *= v
            result.append(prod)
        return Series(result, list(self._index), self.name)

    def resample(self, rule):
        """Minimal resample stub that returns self with apply method."""
        return _Resample(self, rule)

    def idxmin(self):
        """Return index of minimum value."""
        vals = self._data
        min_val = None
        min_idx = self._index[0] if self._index else 0
        for i, v in enumerate(vals):
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                if min_val is None or v < min_val:
                    min_val = v
                    min_idx = self._index[i]
        return min_idx

    def idxmax(self):
        """Return index of maximum value."""
        vals = self._data
        max_val = None
        max_idx = self._index[0] if self._index else 0
        for i, v in enumerate(vals):
            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                if max_val is None or v > max_val:
                    max_val = v
                    max_idx = self._index[i]
        return max_idx

    def prod(self):
        """Product of all values."""
        vals = [v for v in self._data if v is not None and not (isinstance(v, float) and math.isnan(v))]
        result = 1.0
        for v in vals:
            result *= v
        return result

    def cov(self, other, ddof=0):
        if isinstance(other, Series):
            pairs = [(a, b) for a, b in zip(self._data, other._data)
                     if a is not None and b is not None]
            if len(pairs) < 2:
                return 0.0
            ma = sum(a for a, b in pairs) / len(pairs)
            mb = sum(b for a, b in pairs) / len(pairs)
            return sum((a - ma) * (b - mb) for a, b in pairs) / (len(pairs) - ddof)
        return 0.0


class _Resample:
    """Minimal resample stub."""
    def __init__(self, series, rule):
        self._series = series
        self._rule = rule

    def apply(self, func):
        """Apply a function to the resampled data — just applies to whole series as one group."""
        result_val = func(self._series)
        if isinstance(result_val, Series):
            return result_val
        return Series([result_val], list(self._series._index[:1]), self._series.name)

    def mean(self):
        return Series([self._series.mean()], list(self._series._index[:1]), self._series.name)

    def sum(self):
        return Series([self._series.sum()], list(self._series._index[:1]), self._series.name)


class _Row:
    """Acts like a pandas Series row from iloc."""
    def __init__(self, data: dict, idx_name=None):
        self._data = data
        self.name = idx_name

    def __getitem__(self, key):
        return self._data.get(key)

    def get(self, key, default=None):
        return self._data.get(key, default)


class DataFrame:
    """Minimal DataFrame stub with real row access."""
    def __init__(self, data=None, columns=None, index=None):
        if data is None:
            data = {}
        if isinstance(data, list):
            # list of dicts
            if data and isinstance(data[0], dict):
                cols = columns or list(data[0].keys())
                self._data = {k: [row.get(k) for row in data] for k in cols}
                self._columns = cols
            else:
                self._data = {}
                self._columns = columns or []
        elif isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                if isinstance(v, Series):
                    new_data[k] = list(v._data)
                elif isinstance(v, (list, tuple)):
                    new_data[k] = list(v)
                else:
                    new_data[k] = [v]
            self._data = new_data
            self._columns = columns or list(data.keys())
        else:
            self._data = {}
            self._columns = columns or []

        if index is not None:
            self.index = list(index) if not isinstance(index, Index) else index
        else:
            n = len(list(self._data.values())[0]) if self._data else 0
            self.index = list(range(n))

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, new_columns):
        """Rename columns and update internal data keys."""
        old_keys = list(self._data.keys())
        new_cols = list(new_columns)
        if len(old_keys) == len(new_cols):
            new_data = {}
            for old_key, new_key in zip(old_keys, new_cols):
                new_data[new_key] = self._data[old_key]
            self._data = new_data
        self._columns = new_cols

    @property
    def iloc(self):
        return _DFILoc(self)

    @property
    def loc(self):
        return _DFLoc(self)

    @property
    def empty(self):
        if not self._data:
            return True
        first_col = list(self._data.values())[0]
        return len(first_col) == 0

    def __len__(self):
        if not self._data:
            return 0
        return len(list(self._data.values())[0])

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in self._data:
                return Series(self._data[key], list(self.index), name=key)
            return Series()
        if isinstance(key, list):
            # Column selection
            new_data = {k: self._data[k] for k in key if k in self._data}
            return DataFrame(new_data, columns=key, index=self.index)
        return self

    def __setitem__(self, key, value):
        if isinstance(value, Series):
            self._data[key] = list(value._data)
        elif isinstance(value, list):
            self._data[key] = value
        else:
            n = len(self)
            self._data[key] = [value] * n
        if key not in self._columns:
            self._columns = list(self._columns) + [key]

    def _get_row(self, idx):
        """Get a row as _Row by positional index."""
        row_data = {}
        for col in self.columns:
            if col in self._data:
                row_data[col] = self._data[col][idx]
        index_val = self.index[idx] if idx < len(self.index) else idx
        return _Row(row_data, idx_name=index_val)

    def copy(self):
        new_data = {k: list(v) for k, v in self._data.items()}
        return DataFrame(new_data, columns=list(self.columns), index=list(self.index))

    def head(self, n=5):
        new_data = {k: v[:n] for k, v in self._data.items()}
        new_index = self.index[:n] if isinstance(self.index, list) else list(self.index)[:n]
        return DataFrame(new_data, columns=list(self.columns), index=new_index)

    def tail(self, n=5):
        new_data = {k: v[-n:] for k, v in self._data.items()}
        new_index = self.index[-n:] if isinstance(self.index, list) else list(self.index)[-n:]
        return DataFrame(new_data, columns=list(self.columns), index=new_index)

    def rename(self, columns=None, **kwargs):
        if columns:
            new_data = {}
            new_cols = []
            for c in self.columns:
                new_name = columns.get(c, c)
                new_data[new_name] = self._data.get(c, [])
                new_cols.append(new_name)
            return DataFrame(new_data, columns=new_cols, index=list(self.index))
        return self

    def sort_values(self, by, ascending=True, **kwargs):
        if by not in self._data:
            return self
        col = self._data[by]
        indices = sorted(range(len(col)), key=lambda i: col[i] if col[i] is not None else float('inf'),
                        reverse=not ascending)
        new_data = {k: [v[i] for i in indices] for k, v in self._data.items()}
        new_index = [self.index[i] for i in indices] if isinstance(self.index, list) else self.index
        return DataFrame(new_data, columns=list(self.columns), index=new_index)

    def reset_index(self, drop=False):
        return DataFrame(dict(self._data), columns=list(self.columns))

    def iterrows(self):
        for i in range(len(self)):
            yield self.index[i], self._get_row(i)

    def cov(self, ddof=0):
        # Simple 2-column covariance matrix
        if len(self.columns) == 2:
            col_a, col_b = self.columns[0], self.columns[1]
            data_a = self._data.get(col_a, [])
            data_b = self._data.get(col_b, [])
            n = len(data_a)
            if n < 2:
                return DataFrame({col_a: [0, 0], col_b: [0, 0]}, columns=[col_a, col_b], index=[col_a, col_b])
            ma = sum(data_a) / n
            mb = sum(data_b) / n
            var_a = sum((x - ma) ** 2 for x in data_a) / (n - ddof)
            var_b = sum((x - mb) ** 2 for x in data_b) / (n - ddof)
            cov_ab = sum((a - ma) * (b - mb) for a, b in zip(data_a, data_b)) / (n - ddof)
            return DataFrame(
                {col_a: [var_a, cov_ab], col_b: [cov_ab, var_b]},
                columns=[col_a, col_b],
                index=[col_a, col_b]
            )
        return self

    def dropna(self):
        """Drop rows with any None/NaN."""
        if not self._data:
            return self
        n = len(self)
        keep_indices = []
        for i in range(n):
            keep = True
            for col in self.columns:
                v = self._data[col][i]
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    keep = False
                    break
            if keep:
                keep_indices.append(i)
        new_data = {k: [v[i] for i in keep_indices] for k, v in self._data.items()}
        new_index = [self.index[i] for i in keep_indices] if isinstance(self.index, list) else keep_indices
        return DataFrame(new_data, columns=list(self.columns), index=new_index)

    def max(self, axis=None):
        if axis == 1:
            # Row-wise max
            n = len(self)
            result = []
            for i in range(n):
                row_vals = []
                for col in self.columns:
                    v = self._data[col][i]
                    if v is not None and not (isinstance(v, float) and math.isnan(v)):
                        row_vals.append(v)
                result.append(max(row_vals) if row_vals else None)
            return Series(result, list(self.index) if isinstance(self.index, list) else list(range(n)))
        elif axis == 0 or axis is None:
            # Column-wise max
            result = {}
            for col in self.columns:
                vals = [v for v in self._data[col] if v is not None and not (isinstance(v, float) and math.isnan(v))]
                result[col] = max(vals) if vals else None
            return Series(list(result.values()), list(result.keys()))
        return self

    def min(self, axis=None):
        if axis == 1:
            n = len(self)
            result = []
            for i in range(n):
                row_vals = []
                for col in self.columns:
                    v = self._data[col][i]
                    if v is not None and not (isinstance(v, float) and math.isnan(v)):
                        row_vals.append(v)
                result.append(min(row_vals) if row_vals else None)
            return Series(result, list(self.index) if isinstance(self.index, list) else list(range(n)))
        elif axis == 0 or axis is None:
            result = {}
            for col in self.columns:
                vals = [v for v in self._data[col] if v is not None and not (isinstance(v, float) and math.isnan(v))]
                result[col] = min(vals) if vals else None
            return Series(list(result.values()), list(result.keys()))
        return self

    @property
    def values(self):
        return self._data


class Index:
    def __init__(self, data=None):
        self._data = data or []
        self.name = None

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class MultiIndex(Index):
    pass


class _ILoc:
    def __init__(self, series):
        self._series = series

    def __getitem__(self, key):
        if isinstance(key, int):
            if -len(self._series._data) <= key < len(self._series._data):
                return self._series._data[key]
            return 0
        if isinstance(key, slice):
            sliced = self._series._data[key]
            sliced_idx = self._series._index[key]
            return Series(sliced, sliced_idx, self._series.name)
        return self._series


class _DFILoc:
    def __init__(self, df):
        self._df = df

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._df._get_row(key)
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self._df))
            indices = range(start, stop, step)
            new_data = {k: [v[i] for i in indices] for k, v in self._df._data.items()}
            new_index = [self._df.index[i] for i in indices] if isinstance(self._df.index, list) else []
            return DataFrame(new_data, columns=list(self._df.columns), index=new_index)
        return self._df


class _DFLoc:
    def __init__(self, df):
        self._df = df

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            row_key, col_key = key
            # Find row index
            if isinstance(self._df.index, list) and row_key in self._df.index:
                idx = self._df.index.index(row_key)
                if col_key in self._df._data:
                    return self._df._data[col_key][idx]
            return 0.0
        return 0.0


class _Rolling:
    def __init__(self, series, window, min_periods=None):
        self._series = series
        self._window = window
        self._min_periods = min_periods or window

    def _apply(self, func):
        result = []
        data = self._series._data
        for i in range(len(data)):
            start = max(0, i - self._window + 1)
            window_data = [v for v in data[start:i+1]
                          if v is not None and not (isinstance(v, float) and math.isnan(v))]
            if len(window_data) >= self._min_periods:
                result.append(func(window_data))
            else:
                result.append(None)
        return Series(result, list(self._series._index), self._series.name)

    def mean(self):
        return self._apply(lambda w: sum(w) / len(w))

    def std(self, ddof=0):
        def _std(w):
            if len(w) < 2:
                return 0.0
            m = sum(w) / len(w)
            var = sum((x - m) ** 2 for x in w) / (len(w) - ddof)
            return math.sqrt(var)
        return self._apply(_std)

    def min(self):
        return self._apply(lambda w: min(w))

    def max(self):
        return self._apply(lambda w: max(w))

    def sum(self):
        return self._apply(lambda w: sum(w))


class _EWM:
    def __init__(self, series, span=None, alpha=None, min_periods=None, adjust=True):
        self._series = series
        if alpha is not None:
            self._alpha = alpha
        elif span is not None:
            self._alpha = 2.0 / (span + 1)
        else:
            self._alpha = 0.5
        self._min_periods = min_periods or 1
        self._adjust = adjust

    def mean(self):
        data = self._series._data
        result = []
        ewm_val = None
        count = 0
        for i, v in enumerate(data):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                result.append(None)
                continue
            count += 1
            if ewm_val is None:
                ewm_val = v
            else:
                ewm_val = self._alpha * v + (1 - self._alpha) * ewm_val
            if count >= self._min_periods:
                result.append(ewm_val)
            else:
                result.append(None)
        return Series(result, list(self._series._index), self._series.name)


def concat(objs, axis=0, **kwargs):
    if axis == 1:
        # Column-wise concat of Series
        if all(isinstance(o, Series) for o in objs):
            data = {}
            for i, s in enumerate(objs):
                name = s.name or f"col_{i}"
                data[name] = list(s._data)
            idx = objs[0]._index if objs else []
            return DataFrame(data, index=list(idx))
        return DataFrame()
    return DataFrame()
