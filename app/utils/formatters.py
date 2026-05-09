"""
formatters.py
==============

Helpery formatujące + mapy kolorów. Polskie etykiety dla setupu/ryzyka itd.
"""

from __future__ import annotations

from app.i18n import strings_pl as t


def format_price(value: float) -> str:
    if value is None:
        return "—"
    if value >= 1000:
        return f"${value:,.2f}"
    if value >= 1:
        return f"${value:.2f}"
    return f"${value:.4f}"


def format_volume(value: float) -> str:
    if value is None or value == 0:
        return "—"
    if value >= 1e9:
        return f"{value / 1e9:.2f} mld"
    if value >= 1e6:
        return f"{value / 1e6:.2f} mln"
    if value >= 1e3:
        return f"{value / 1e3:.2f} tys."
    return f"{value:.0f}"


def format_market_cap(value) -> str:
    if not value:
        return "—"
    if value >= 1e12:
        return f"{value / 1e12:.2f} bln USD"
    if value >= 1e9:
        return f"{value / 1e9:.2f} mld USD"
    if value >= 1e6:
        return f"{value / 1e6:.2f} mln USD"
    return f"{value:,.0f} USD"


def color_for_score(score: float) -> str:
    if score >= 8:    return "#26a69a"
    if score >= 6.5:  return "#66bb6a"
    if score >= 5:    return "#ffb300"
    if score >= 3.5:  return "#ff7043"
    return "#ef5350"


def color_for_risk(risk_level: str) -> str:
    return {"Low": "#26a69a", "Medium": "#ffb300",
            "High": "#ff7043", "Extreme": "#ef5350"}.get(risk_level, "#9e9e9e")


def color_for_grade(grade: str) -> str:
    return {"A+": "#26a69a", "A": "#66bb6a", "B": "#9ccc65",
            "C": "#ffb300", "D": "#ef5350"}.get(grade, "#9e9e9e")


def pl_trend(label: str) -> str:
    return t.TREND_LABELS.get(label, label)


def pl_momentum(label: str) -> str:
    return t.MOMENTUM_LABELS.get(label, label)


def pl_risk(label: str) -> str:
    return t.RISK_LABELS.get(label, label)
