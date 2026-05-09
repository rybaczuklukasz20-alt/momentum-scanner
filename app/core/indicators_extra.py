"""
indicators_extra.py
=====================

Dodatkowe wskaźniki techniczne (poza zestawem podstawowym z indicators.py):

- Bollinger Bands (BB) — pasma zmienności wokół 20-okresowej SMA
- ADX (Average Directional Index) — siła trendu (kierunek osobno: +DI / -DI)
- OBV (On-Balance Volume) — kumulowany wolumen kierunkowy
- VWAP (Volume-Weighted Average Price) — obliczany rolling lub od początku

Wszystkie funkcje dostają OHLCV DataFrame i zwracają Series lub DataFrame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def bollinger_bands(close: pd.Series, length: int = 20,
                    num_std: float = 2.0) -> pd.DataFrame:
    """
    Klasyczne wstęgi Bollingera: środkowa SMA(20) ± 2 odchylenia standardowe.
    Zwraca DataFrame z kolumnami: BB_Mid, BB_Upper, BB_Lower, BB_Width.
    """
    mid = close.rolling(window=length, min_periods=length).mean()
    std = close.rolling(window=length, min_periods=length).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower) / mid  # względna szerokość — przydatna do "squeeze"
    return pd.DataFrame({
        "BB_Mid": mid,
        "BB_Upper": upper,
        "BB_Lower": lower,
        "BB_Width": width,
    })


# ---------------------------------------------------------------------------
# ADX — Average Directional Index (Wilder)
# ---------------------------------------------------------------------------

def adx(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    """
    ADX + +DI/-DI w klasycznej formule Wildera.

    Interpretacja ADX:
      < 20  — brak trendu / chaos
      20-25 — słaby trend
      25-50 — silny trend
      > 50  — bardzo silny trend (rzadkie, często przed wyczerpaniem)

    Kierunek czytamy z porównania +DI vs -DI, nie samego ADX.
    """
    high, low, close = df["High"], df["Low"], df["Close"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
                        index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
                         index=df.index)

    # True Range (jak w ATR)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Wilder smoothing (alpha = 1/length)
    atr_w = tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / length, adjust=False).mean() / atr_w)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / length, adjust=False).mean() / atr_w)

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    adx_val = dx.ewm(alpha=1 / length, adjust=False).mean()

    return pd.DataFrame({
        "ADX": adx_val,
        "+DI": plus_di,
        "-DI": minus_di,
    })


# ---------------------------------------------------------------------------
# OBV — On-Balance Volume
# ---------------------------------------------------------------------------

def obv(df: pd.DataFrame) -> pd.Series:
    """
    OBV = kumulowany wolumen, gdzie dni wzrostowe dodają, spadkowe odejmują.
    Dywergencje OBV vs cena to klasyczny sygnał akumulacji/dystrybucji.
    """
    close = df["Close"]
    volume = df["Volume"]
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


# ---------------------------------------------------------------------------
# VWAP — Volume-Weighted Average Price
# ---------------------------------------------------------------------------

def vwap(df: pd.DataFrame, length: int | None = None) -> pd.Series:
    """
    VWAP klasyczny: sum(typical_price * volume) / sum(volume).

    Jeśli `length` jest None → kumulacja od początku zakresu danych
    (przybliżenie 'sesyjnego' VWAP dla dziennego TF).

    Jeśli `length` ma wartość → rolling VWAP z oknem N sesji,
    co daje bardziej responsywną linię na wykresach dziennych.
    """
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    volume = df["Volume"]
    pv = typical * volume

    if length is None:
        return pv.cumsum() / volume.cumsum()

    return (pv.rolling(window=length, min_periods=length).sum() /
            volume.rolling(window=length, min_periods=length).sum())


# ---------------------------------------------------------------------------
# Helper: dodanie wszystkich extra wskaźników do enriched DataFrame
# ---------------------------------------------------------------------------

def append_extras(enriched: pd.DataFrame, vwap_length: int = 20) -> pd.DataFrame:
    """Wzbogaca DataFrame o BB / ADX / OBV / VWAP. Zwraca nowy DataFrame."""
    out = enriched.copy()

    bb = bollinger_bands(out["Close"], length=20, num_std=2.0)
    out["BB_Mid"]   = bb["BB_Mid"]
    out["BB_Upper"] = bb["BB_Upper"]
    out["BB_Lower"] = bb["BB_Lower"]
    out["BB_Width"] = bb["BB_Width"]

    adx_df = adx(out, length=14)
    out["ADX"]   = adx_df["ADX"]
    out["+DI"]   = adx_df["+DI"]
    out["-DI"]   = adx_df["-DI"]

    out["OBV"]  = obv(out)
    out["VWAP"] = vwap(out, length=vwap_length)

    return out
