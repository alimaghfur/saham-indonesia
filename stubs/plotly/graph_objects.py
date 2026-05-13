"""Stub for plotly.graph_objects module (used for `import plotly.graph_objects as go`)."""
from plotly import graph_objects as _go

Figure = _go.Figure
Candlestick = _go.Candlestick
Ohlc = _go.Ohlc
Scatter = _go.Scatter
Bar = _go.Bar
Pie = _go.Pie
Layout = _go.Layout


class layout:
    """Namespace for go.layout.Template etc."""
    class Template:
        def __init__(self, **kwargs):
            pass
