"""
indicators.py
==============

Pure-pandas technical indicators. We deliberately implement the math in
plain pandas/numpy rather than relying solely on `pandas-ta` (which is
listed as an optional dependency for advanced users), because:

  1. It avoids version-incompatibility headaches on Python 3.12+.
  2. Every formula is auditable for the user — no black boxes.
  3. It keeps the install lean for beginners.

Each function takes a DataFrame with the canonical OHLCV columns and
returns either a Series (single line) or a DataFrame (multi-column).

If `pandas-ta` is installed it can be swapped in trivially — see the
__main__ block at the bottom for an example.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

def ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=length, min_periods=length).mean()


# ---------------------------------------------------------------------------
# RSI (Wilder's smoothing) + RSI moving averages
# ---------------------------------------------------------------------------

def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """
    Relative Strength Index using Wilder's exponential smoothing — the
    classic formulation, identical to TradingView's default RSI.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder smoothing == EMA with alpha = 1/length
    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi_values = 100 - (100 / (1 + rs))
    return rsi_values.fillna(50.0)  # Neutral fill for early bars


def rsi_with_mas(close: pd.Series, length: int = 14,
                 fast: int = 9, slow: int = 21) -> pd.DataFrame:
    """Return a DataFrame with RSI and two SMAs of RSI (default 9 & 21)."""
    r = rsi(close, length)
    return pd.DataFrame({
        "RSI": r,
        f"RSI_MA_{fast}": r.rolling(fast).mean(),
        f"RSI_MA_{slow}": r.rolling(slow).mean(),
    })


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def macd(close: pd.Series, fast: int = 12, slow: int = 26,
         signal: int = 9) -> pd.DataFrame:
    """Standard MACD: 12/26/9."""
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histogram": histogram,
    })


# ---------------------------------------------------------------------------
# Volume analytics
# ---------------------------------------------------------------------------

def relative_volume(volume: pd.Series, length: int = 20) -> pd.Series:
    """RVOL = today's volume / average volume over `length` days."""
    avg = volume.rolling(window=length, min_periods=length).mean()
    return volume / avg.replace(0.0, np.nan)


def volume_spike_flags(volume: pd.Series, length: int = 20,
                       threshold: float = 2.0) -> pd.Series:
    """Boolean series: True wherever volume >= threshold * its rolling avg."""
    rvol = relative_volume(volume, length)
    return rvol >= threshold


# ---------------------------------------------------------------------------
# ATR (used for trend strength normalization)
# ---------------------------------------------------------------------------

def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Average True Range — Wilder smoothing."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


# ---------------------------------------------------------------------------
# Trend strength (custom: combines slope of EMA20 + EMA stack alignment)
# ---------------------------------------------------------------------------

def trend_strength(close: pd.Series) -> Tuple[float, str]:
    """
    Returns a 0-100 trend strength score and a human label.

    Methodology:
        - 50 base points for "EMA stack" alignment (20 > 50 > 200 = strong up).
        - Up to 50 points scaled by the 20-day slope of EMA20 normalized by
          recent ATR — so it rewards a steady, well-supported up-move and
          penalizes choppy or down-sloping action.
    """
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    ema200 = ema(close, 200)

    if len(close) < 200 or ema200.isna().iloc[-1]:
        return 0.0, "Insufficient data"

    last_close = close.iloc[-1]
    score = 0.0

    # --- Stack alignment (max 50) ---
    if ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
        score += 50  # Bullish stack
    elif ema20.iloc[-1] < ema50.iloc[-1] < ema200.iloc[-1]:
        score -= 50  # Bearish stack
    else:
        # Mixed — partial credit based on how many MAs price is above
        above = sum([last_close > ema20.iloc[-1],
                     last_close > ema50.iloc[-1],
                     last_close > ema200.iloc[-1]])
        score += (above - 1.5) * 15  # -22.5 to +22.5

    # --- Slope component (max ±50) ---
    slope = ema20.diff(20).iloc[-1] / 20  # avg daily change over last 20 bars
    recent_atr = (close.diff().abs().rolling(20).mean()).iloc[-1]
    if recent_atr and not np.isnan(recent_atr):
        normalized_slope = slope / recent_atr  # roughly -1 to +1 in normal markets
        score += float(np.clip(normalized_slope * 50, -50, 50))

    # Clamp to 0-100 for display (negative trends are floored at 0 — we
    # surface direction via the label).
    raw_score = score
    display_score = float(np.clip((raw_score + 50), 0, 100))

    if raw_score >= 60:
        label = "Strong Uptrend"
    elif raw_score >= 25:
        label = "Moderate Uptrend"
    elif raw_score >= -25:
        label = "Sideways / Choppy"
    elif raw_score >= -60:
        label = "Moderate Downtrend"
    else:
        label = "Strong Downtrend"

    return display_score, label


# ---------------------------------------------------------------------------
# Support / resistance via swing pivots
# ---------------------------------------------------------------------------

def swing_levels(df: pd.DataFrame, lookback: int = 5,
                 max_levels: int = 3, cluster_pct: float = 0.02
                 ) -> Tuple[list, list]:
    """
    Identify support and resistance using fractal-style swing pivots.

    A swing-high bar has the highest High over `lookback` bars on each side.
    Levels within `cluster_pct` (default 2%) of each other are merged.

    Returns (supports, resistances) — each a list of price levels closest
    to the latest close, capped at `max_levels`.
    """
    highs, lows = df["High"], df["Low"]
    last_close = df["Close"].iloc[-1]

    swing_highs, swing_lows = [], []

    # Need 2*lookback+1 bars to define a pivot
    for i in range(lookback, len(df) - lookback):
        window_h = highs.iloc[i - lookback : i + lookback + 1]
        window_l = lows.iloc[i - lookback : i + lookback + 1]
        if highs.iloc[i] == window_h.max():
            swing_highs.append(highs.iloc[i])
        if lows.iloc[i] == window_l.min():
            swing_lows.append(lows.iloc[i])

    def _cluster(levels: list) -> list:
        """Merge nearby levels by averaging within `cluster_pct` bands."""
        if not levels:
            return []
        levels = sorted(levels)
        clustered = [[levels[0]]]
        for lvl in levels[1:]:
            if abs(lvl - clustered[-1][-1]) / clustered[-1][-1] <= cluster_pct:
                clustered[-1].append(lvl)
            else:
                clustered.append([lvl])
        return [float(np.mean(c)) for c in clustered]

    swing_highs = _cluster(swing_highs)
    swing_lows = _cluster(swing_lows)

    # Resistances are clusters above current price; supports are below.
    resistances = sorted([h for h in swing_highs if h > last_close])[:max_levels]
    supports = sorted([l for l in swing_lows if l < last_close], reverse=True)[:max_levels]

    return supports, resistances


# ---------------------------------------------------------------------------
# Breakout detection
# ---------------------------------------------------------------------------

@dataclass
class BreakoutInfo:
    is_breakout: bool
    direction: str  # "up", "down", or "none"
    level: float | None
    days_since_breakout: int | None


def detect_breakout(df: pd.DataFrame, lookback: int = 50,
                    confirm_bars: int = 2) -> BreakoutInfo:
    """
    Flags a breakout when the most recent close exceeds the prior `lookback`-
    bar high (or falls below the lookback low), and stays through the close
    of `confirm_bars` consecutive sessions.
    """
    if len(df) < lookback + confirm_bars + 1:
        return BreakoutInfo(False, "none", None, None)

    closes = df["Close"]

    # Range of the prior lookback window (excluding the most recent confirm window)
    prior = df.iloc[-(lookback + confirm_bars) : -confirm_bars]
    prior_high = prior["High"].max()
    prior_low = prior["Low"].min()

    recent_closes = closes.iloc[-confirm_bars:]
    if (recent_closes > prior_high).all():
        return BreakoutInfo(True, "up", float(prior_high), confirm_bars)
    if (recent_closes < prior_low).all():
        return BreakoutInfo(True, "down", float(prior_low), confirm_bars)

    return BreakoutInfo(False, "none", None, None)


# ---------------------------------------------------------------------------
# Momentum strength (composite)
# ---------------------------------------------------------------------------

def momentum_strength(df: pd.DataFrame) -> Tuple[float, str]:
    """
    Composite momentum reading on a 0-100 scale.

    Combines:
      - 1-month and 3-month return percentile (weighted 40%)
      - Distance above EMA50 in ATR units (weighted 30%)
      - MACD histogram sign + magnitude (weighted 15%)
      - RSI level vs 50 line (weighted 15%)

    Designed to mirror the kind of "is this thing moving?" gut-check a
    momentum trader makes before drilling into chart structure.
    """
    if len(df) < 90:
        return 0.0, "Insufficient data"

    close = df["Close"]
    last = close.iloc[-1]

    # --- Returns component ---
    ret_1m = (last / close.iloc[-21] - 1) * 100 if len(close) >= 22 else 0
    ret_3m = (last / close.iloc[-63] - 1) * 100 if len(close) >= 64 else 0
    # Map -20%..+40% return to 0..100, then average
    returns_score = float(np.clip(((ret_1m + 20) / 60) * 50 +
                                  ((ret_3m + 20) / 60) * 50, 0, 100))

    # --- Distance above EMA50 in ATR units ---
    ema50_val = ema(close, 50).iloc[-1]
    atr_val = atr(df, 14).iloc[-1]
    if atr_val and not np.isnan(atr_val):
        atr_distance = (last - ema50_val) / atr_val  # typically -3..+10
        distance_score = float(np.clip((atr_distance + 3) / 13 * 100, 0, 100))
    else:
        distance_score = 50.0

    # --- MACD histogram ---
    macd_df = macd(close)
    hist = macd_df["Histogram"].iloc[-1]
    # Normalize by close price for a relative reading
    hist_pct = (hist / last) * 100 if last else 0
    macd_score = float(np.clip((hist_pct + 1) / 2 * 100, 0, 100))

    # --- RSI ---
    rsi_val = rsi(close).iloc[-1]
    # 30-70 is the "sweet spot" — we want momentum but not blow-off
    if rsi_val < 30:
        rsi_score = (rsi_val / 30) * 30
    elif rsi_val <= 70:
        rsi_score = 30 + ((rsi_val - 30) / 40) * 60
    else:  # >70 — penalize for being extended
        rsi_score = 90 - ((rsi_val - 70) / 30) * 40

    composite = (returns_score * 0.40 +
                 distance_score * 0.30 +
                 macd_score * 0.15 +
                 rsi_score * 0.15)

    if composite >= 75:
        label = "Powerful"
    elif composite >= 60:
        label = "Strong"
    elif composite >= 45:
        label = "Building"
    elif composite >= 30:
        label = "Weak"
    else:
        label = "Absent"

    return float(composite), label


# ---------------------------------------------------------------------------
# Single helper that bundles everything for downstream consumers
# ---------------------------------------------------------------------------

def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the original df with all indicator columns appended. This is
    the canonical "enriched" dataframe used by the chart and the AI analyst.
    """
    out = df.copy()
    close = out["Close"]
    volume = out["Volume"]

    out["EMA20"] = ema(close, 20)
    out["EMA50"] = ema(close, 50)
    out["EMA200"] = ema(close, 200)

    out["RSI"] = rsi(close, 14)
    out["RSI_MA9"] = out["RSI"].rolling(9).mean()
    out["RSI_MA21"] = out["RSI"].rolling(21).mean()

    macd_df = macd(close)
    out["MACD"] = macd_df["MACD"]
    out["MACD_Signal"] = macd_df["Signal"]
    out["MACD_Hist"] = macd_df["Histogram"]

    out["RVOL"] = relative_volume(volume, 20)
    out["VolSpike"] = volume_spike_flags(volume, 20, 2.0)

    out["ATR"] = atr(out, 14)

    # Nowe wskaźniki: Bollinger, ADX, OBV, VWAP
    bb = bollinger_bands(close, 20, 2.0)
    out["BB_Upper"] = bb["BB_Upper"]
    out["BB_Middle"] = bb["BB_Middle"]
    out["BB_Lower"] = bb["BB_Lower"]
    out["BB_Width"] = bb["BB_Width"]

    adx_df = adx(out, 14)
    out["ADX"] = adx_df["ADX"]
    out["+DI"] = adx_df["+DI"]
    out["-DI"] = adx_df["-DI"]

    out["OBV"] = obv(out)
    out["VWAP"] = vwap(out)

    return out


# ---------------------------------------------------------------------------
# Wstęgi Bollingera
# ---------------------------------------------------------------------------

def bollinger_bands(close: pd.Series, length: int = 20,
                    num_std: float = 2.0) -> pd.DataFrame:
    """
    Klasyczne wstęgi Bollingera: SMA + 2 odchylenia standardowe.
    Zwraca DataFrame z kolumnami BB_Upper, BB_Middle, BB_Lower, BB_Width.
    """
    middle = close.rolling(window=length, min_periods=length).mean()
    std = close.rolling(window=length, min_periods=length).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    width = (upper - lower) / middle  # znormalizowana szerokość
    return pd.DataFrame({
        "BB_Upper": upper,
        "BB_Middle": middle,
        "BB_Lower": lower,
        "BB_Width": width,
    })


# ---------------------------------------------------------------------------
# ADX — Average Directional Index (siła trendu, niezależnie od kierunku)
# ---------------------------------------------------------------------------

def adx(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    """
    ADX z +DI i -DI. ADX > 25 = silny trend, < 20 = brak trendu.
    Zwraca DataFrame z kolumnami ADX, +DI, -DI.
    """
    high, low, close = df["High"], df["Low"], df["Close"]

    # True Range
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Directional Movement
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # Wilder smoothing
    atr_v = tr.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1/length, adjust=False, min_periods=length).mean() / atr_v
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1/length, adjust=False, min_periods=length).mean() / atr_v

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_v = dx.ewm(alpha=1/length, adjust=False, min_periods=length).mean()

    return pd.DataFrame({
        "ADX": adx_v,
        "+DI": plus_di,
        "-DI": minus_di,
    })


# ---------------------------------------------------------------------------
# OBV — On Balance Volume (skumulowany wolumen kierunkowy)
# ---------------------------------------------------------------------------

def obv(df: pd.DataFrame) -> pd.Series:
    """
    OBV: kumulowany wolumen, dodawany w dni wzrostowe i odejmowany
    w dni spadkowe. Rozbieżność OBV vs cena to klasyczny sygnał.
    """
    direction = np.sign(df["Close"].diff().fillna(0))
    return (direction * df["Volume"]).cumsum()


# ---------------------------------------------------------------------------
# VWAP — Volume Weighted Average Price
# ---------------------------------------------------------------------------

def vwap(df: pd.DataFrame) -> pd.Series:
    """
    VWAP liczone od początku serii (rolling cumulative).
    Dla danych dziennych zwraca cenę średnio ważoną wolumenem od start
    do danej sesji — przydatne do oceny gdzie 'siedzi' duży kapitał.
    """
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    pv = typical * df["Volume"]
    return pv.cumsum() / df["Volume"].cumsum().replace(0, np.nan)
