"""
ai_analyst.py
==============

Silnik analityczny — deterministyczny, regułowy "mózg" aplikacji.
Zwracane teksty są po polsku (przez słownik strings_pl).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd

from app.core.indicators import (
    compute_all,
    detect_breakout,
    momentum_strength,
    swing_levels,
    trend_strength,
)
from app.i18n import strings_pl as t


@dataclass
class AnalysisReport:
    technical_score: float
    momentum_rating: str       # klucz EN — UI tłumaczy
    trend_label: str           # klucz EN — UI tłumaczy
    risk_level: str            # klucz EN — UI tłumaczy
    setup_quality: str         # A+/A/B/C/D
    trend_direction: str       # PL
    momentum_quality: str      # PL
    institutional_read: str    # PL
    extension_read: str        # PL
    volume_confirmation: str   # PL
    health_assessment: str     # PL
    bullish_signals: List[str] = field(default_factory=list)  # PL
    bearish_signals: List[str] = field(default_factory=list)  # PL
    supports: List[float] = field(default_factory=list)
    resistances: List[float] = field(default_factory=list)
    last_close: float = 0.0


def _safe_last(series: pd.Series, default: float = float("nan")) -> float:
    s = series.dropna()
    return float(s.iloc[-1]) if len(s) else default


def analyze(df: pd.DataFrame) -> AnalysisReport:
    enriched = compute_all(df)

    last_close = _safe_last(enriched["Close"])
    ema20_v    = _safe_last(enriched["EMA20"])
    ema50_v    = _safe_last(enriched["EMA50"])
    ema200_v   = _safe_last(enriched["EMA200"])
    rsi_v      = _safe_last(enriched["RSI"])
    rsi_ma9_v  = _safe_last(enriched["RSI_MA9"])
    rsi_ma21_v = _safe_last(enriched["RSI_MA21"])
    macd_v     = _safe_last(enriched["MACD"])
    macd_sig_v = _safe_last(enriched["MACD_Signal"])
    macd_hist  = _safe_last(enriched["MACD_Hist"])
    rvol_v     = _safe_last(enriched["RVOL"])
    atr_v      = _safe_last(enriched["ATR"])

    trend_pts, trend_lbl = trend_strength(enriched["Close"])
    mom_pts, mom_lbl     = momentum_strength(enriched)
    supports, resistances = swing_levels(enriched)
    breakout = detect_breakout(enriched)

    bullish: List[str] = []
    bearish: List[str] = []

    # --- Trend ---
    if last_close > ema20_v > ema50_v > ema200_v:
        trend_direction = t.TREND_BULLISH_STACK
        bullish.append(t.BULL_EMA_STACK)
    elif last_close < ema20_v < ema50_v < ema200_v:
        trend_direction = t.TREND_BEARISH_STACK
        bearish.append(t.BEAR_EMA_STACK)
    elif last_close > ema200_v and last_close < ema20_v:
        trend_direction = t.TREND_LT_UP_ST_DOWN
    else:
        trend_direction = t.TREND_MIXED

    # --- Momentum ---
    parts = []
    if rsi_v >= 70:
        parts.append(t.RSI_OVERBOUGHT.format(rsi=rsi_v))
        bearish.append(t.BEAR_RSI_OVERBOUGHT.format(rsi=rsi_v))
    elif rsi_v >= 55 and rsi_ma9_v > rsi_ma21_v:
        parts.append(t.RSI_BULL_ZONE.format(rsi=rsi_v))
        bullish.append(t.BULL_RSI_ZONE)
    elif 45 <= rsi_v < 55:
        parts.append(t.RSI_NEUTRAL.format(rsi=rsi_v))
    elif rsi_v <= 30:
        parts.append(t.RSI_OVERSOLD.format(rsi=rsi_v))
        bearish.append(t.BEAR_RSI_OVERSOLD.format(rsi=rsi_v))
    else:
        parts.append(t.RSI_BELOW_50.format(rsi=rsi_v))

    if macd_v > macd_sig_v and macd_hist > 0:
        if macd_v > 0:
            parts.append(t.MACD_BULL_ABOVE_ZERO)
            bullish.append(t.BULL_MACD_POS)
        else:
            parts.append(t.MACD_BULL_BELOW_ZERO)
    elif macd_v < macd_sig_v:
        parts.append(t.MACD_BEAR)
        bearish.append(t.BEAR_MACD_NEG)
    momentum_quality = " ".join(parts)

    # --- Akumulacja instytucjonalna ---
    recent = enriched.tail(30).copy()
    recent["UpDay"] = recent["Close"] > recent["Close"].shift(1)
    up_vol = recent.loc[recent["UpDay"], "Volume"].sum()
    down_vol = recent.loc[~recent["UpDay"], "Volume"].sum()

    last_10 = enriched.tail(10)
    last_bar_up = enriched["Close"].iloc[-1] > enriched["Close"].iloc[-2]
    last_bar_vol = enriched["Volume"].iloc[-1]
    max_down_vol_10 = (
        last_10.loc[last_10["Close"] < last_10["Close"].shift(1), "Volume"].max()
        if (last_10["Close"] < last_10["Close"].shift(1)).any() else 0
    )
    pocket_pivot = last_bar_up and last_bar_vol > max_down_vol_10

    if up_vol > down_vol * 1.4 and last_close > ema50_v:
        institutional_read = t.INST_ACCUMULATION
        bullish.append(t.BULL_ACCUMULATION)
    elif down_vol > up_vol * 1.4:
        institutional_read = t.INST_DISTRIBUTION
        bearish.append(t.BEAR_DISTRIBUTION)
    else:
        institutional_read = t.INST_BALANCED
    if pocket_pivot:
        institutional_read += t.INST_POCKET_PIVOT
        bullish.append(t.BULL_POCKET_PIVOT)

    # --- Rozciągnięcie ---
    atr_above_ema50 = (
        (last_close - ema50_v) / atr_v
        if (atr_v and not np.isnan(atr_v)) else 0
    )
    pct_above_ema20 = (last_close / ema20_v - 1) * 100 if ema20_v else 0

    if atr_above_ema50 >= 6:
        extension_read = t.EXT_CLIMACTIC.format(atr=atr_above_ema50)
        bearish.append(t.BEAR_EXTENDED)
    elif atr_above_ema50 >= 3:
        extension_read = t.EXT_MODERATE.format(atr=atr_above_ema50)
    elif -1 <= atr_above_ema50 < 3 and last_close > ema50_v:
        extension_read = t.EXT_SWEET_SPOT
        bullish.append(t.BULL_HEALTHY_DISTANCE)
    elif last_close < ema50_v:
        extension_read = t.EXT_BELOW_EMA50
    else:
        extension_read = t.EXT_NEAR_EMA50.format(pct=pct_above_ema20)

    # --- Wolumen ---
    last_5_rvol = enriched["RVOL"].tail(5).mean()
    if rvol_v >= 2.0:
        volume_confirmation = t.VOL_SPIKE.format(rvol=rvol_v)
        bullish.append(t.BULL_VOL_SPIKE.format(rvol=rvol_v))
    elif last_5_rvol >= 1.3 and last_close > ema20_v:
        volume_confirmation = t.VOL_EXPANDING.format(rvol=last_5_rvol)
        bullish.append(t.BULL_VOL_EXPAND)
    elif last_5_rvol < 0.8 and last_close > ema20_v:
        volume_confirmation = t.VOL_LIGHT.format(rvol=last_5_rvol)
        bearish.append(t.BEAR_LIGHT_VOL)
    else:
        volume_confirmation = t.VOL_NORMAL.format(rvol=last_5_rvol)

    # --- Wybicie ---
    breakout_note = ""
    if breakout.is_breakout and breakout.direction == "up":
        breakout_note = t.BREAKOUT_NOTE_UP.format(level=breakout.level)
        bullish.append(t.BULL_BREAKOUT.format(level=breakout.level))
    elif breakout.is_breakout and breakout.direction == "down":
        breakout_note = t.BREAKOUT_NOTE_DOWN.format(level=breakout.level)
        bearish.append(t.BEAR_BREAKDOWN.format(level=breakout.level))

    # --- Zdrowie ---
    if trend_pts >= 75 and mom_pts >= 60 and atr_above_ema50 < 6:
        health_assessment = t.HEALTH_GOOD + breakout_note
    elif trend_pts >= 60 and atr_above_ema50 >= 6:
        health_assessment = t.HEALTH_EXTENDED + breakout_note
    elif trend_pts < 40 and rsi_v < 50:
        health_assessment = t.HEALTH_DANGEROUS + breakout_note
    else:
        health_assessment = t.HEALTH_MIXED + breakout_note

    # --- Score / risk / grade ---
    score = _calculate_technical_score(
        trend_pts=trend_pts, momentum_pts=mom_pts, rsi_v=rsi_v,
        atr_above_ema50=atr_above_ema50, breakout=breakout,
        bullish=bullish, bearish=bearish,
    )
    risk_level = _calculate_risk(rsi_v, atr_above_ema50, trend_pts, last_close, ema200_v)
    setup_quality = _setup_letter_grade(score, len(bullish), len(bearish))

    return AnalysisReport(
        technical_score=score,
        momentum_rating=mom_lbl,
        trend_label=trend_lbl,
        risk_level=risk_level,
        setup_quality=setup_quality,
        trend_direction=trend_direction,
        momentum_quality=momentum_quality,
        institutional_read=institutional_read,
        extension_read=extension_read,
        volume_confirmation=volume_confirmation,
        health_assessment=health_assessment,
        bullish_signals=bullish,
        bearish_signals=bearish,
        supports=supports,
        resistances=resistances,
        last_close=last_close,
    )


def _calculate_technical_score(*, trend_pts, momentum_pts, rsi_v,
                               atr_above_ema50, breakout, bullish, bearish):
    raw = 5.0
    raw += (trend_pts - 50) / 25
    raw += (momentum_pts - 50) / 25
    if 55 <= rsi_v <= 70:    raw += 1.0
    elif 50 <= rsi_v < 55:   raw += 0.4
    elif rsi_v > 75:         raw -= 0.5
    elif rsi_v < 35:         raw -= 1.0
    if atr_above_ema50 >= 6:    raw -= 1.5
    elif atr_above_ema50 >= 4:  raw -= 0.5
    if breakout.is_breakout and breakout.direction == "up":   raw += 1.0
    elif breakout.is_breakout and breakout.direction == "down": raw -= 1.5
    raw += 0.2 * (len(bullish) - len(bearish))
    return float(np.clip(round(raw, 1), 1.0, 10.0))


def _calculate_risk(rsi_v, atr_above_ema50, trend_pts, last_close, ema200):
    s = 0
    if rsi_v >= 75:    s += 2
    elif rsi_v >= 70:  s += 1
    if atr_above_ema50 >= 6:    s += 2
    elif atr_above_ema50 >= 4:  s += 1
    if trend_pts < 35:    s += 2
    elif trend_pts < 50:  s += 1
    if not np.isnan(ema200) and last_close < ema200: s += 1
    if s >= 5: return "Extreme"
    if s >= 3: return "High"
    if s >= 1: return "Medium"
    return "Low"


def _setup_letter_grade(score, n_bull, n_bear):
    if score >= 9 and n_bull >= 4 and n_bear <= 1: return "A+"
    if score >= 8:   return "A"
    if score >= 6.5: return "B"
    if score >= 5:   return "C"
    return "D"
