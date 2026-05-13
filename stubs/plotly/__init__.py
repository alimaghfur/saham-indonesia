"""Minimal plotly stub for testing charting module."""
from __future__ import annotations


class graph_objects:
    """Stub for plotly.graph_objects."""

    class Figure:
        def __init__(self, data=None, layout=None, **kwargs):
            self.data = data or []
            self._layout = layout or {}
            self._traces = []

        def add_trace(self, trace, row=None, col=None):
            self._traces.append(trace)

        def add_hline(self, **kwargs):
            pass

        def add_hrect(self, **kwargs):
            pass

        def add_annotation(self, **kwargs):
            pass

        def update_layout(self, **kwargs):
            self._layout.update(kwargs)

        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        @property
        def layout(self):
            return self._layout

    class Candlestick:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Ohlc:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Scatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Bar:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Pie:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class layout:
        class Template:
            def __init__(self, **kwargs):
                pass

    class Layout:
        class Template:
            def __init__(self, **kwargs):
                pass

        def __init__(self, **kwargs):
            pass


class io:
    """Stub for plotly.io."""
    class _Templates:
        default = "plotly"
        def __setattr__(self, key, value):
            object.__setattr__(self, key, value)
        def __setitem__(self, key, value):
            pass
    templates = _Templates()


class subplots:
    """Stub for plotly.subplots."""

    @staticmethod
    def make_subplots(**kwargs):
        return graph_objects.Figure()
