"""Valuation models — DCF, Graham Number, relative valuation.

Skeleton — implement as modules stabilize.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DCFInputs:
    """Inputs for a basic two-stage DCF."""

    fcf_last: float
    growth_high: float = 0.10        # stage-1 growth
    growth_terminal: float = 0.03    # stage-2 growth (perpetuity)
    discount_rate: float = 0.10      # WACC
    years_high: int = 5
    shares_outstanding: int = 1


def dcf_fair_value(inputs: DCFInputs) -> float:
    """Two-stage DCF fair value per share.

    TODO: add mid-year convention, sensitivity analysis, scenario table.
    """
    if inputs.discount_rate <= inputs.growth_terminal:
        raise ValueError("discount_rate must exceed growth_terminal")

    pv_stage1 = 0.0
    fcf = inputs.fcf_last
    for t in range(1, inputs.years_high + 1):
        fcf = fcf * (1 + inputs.growth_high)
        pv_stage1 += fcf / (1 + inputs.discount_rate) ** t

    terminal_fcf = fcf * (1 + inputs.growth_terminal)
    terminal_value = terminal_fcf / (inputs.discount_rate - inputs.growth_terminal)
    pv_terminal = terminal_value / (1 + inputs.discount_rate) ** inputs.years_high

    equity_value = pv_stage1 + pv_terminal
    return equity_value / max(1, inputs.shares_outstanding)


def graham_number(eps: float, bvps: float) -> float:
    """Benjamin Graham's fair-value formula: sqrt(22.5 * EPS * BVPS).

    Returns 0 if either input is non-positive (the formula assumes profits).
    """
    if eps <= 0 or bvps <= 0:
        return 0.0
    return (22.5 * eps * bvps) ** 0.5
