"""
data_fetcher.py
================

Downloads OHLCV market data from Yahoo Finance via the `yfinance` library,
with simple in-memory caching via Streamlit's cache_data decorator so that
re-running indicators on the same ticker is fast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import streamlit as st
import yfinance as yf


@dataclass
class TickerData:
    """Container for everything we know about a ticker."""

    symbol: str
    history: pd.DataFrame  # OHLCV with DatetimeIndex
    info: dict              # Yahoo metadata (name, sector, market cap, etc.)


# Streamlit cache: 5-minute TTL keeps the UI snappy without serving truly stale prices.
@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[TickerData]:
    """
    Fetch historical OHLCV data and metadata for `symbol`.

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. "PLTR", "NVDA", "HIMS".
    period : str
        yfinance period string. Default "1y" (one year of daily candles).
    interval : str
        yfinance interval. Default "1d" (daily).

    Returns
    -------
    TickerData or None
        None if the ticker is invalid or no data is returned.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        return None

    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval, auto_adjust=False)

        if history is None or history.empty:
            return None

        # yfinance occasionally returns timezone-aware indexes, which Plotly handles
        # better when normalized to naive UTC for display purposes.
        if history.index.tz is not None:
            history.index = history.index.tz_localize(None)

        # Normalize columns: yfinance may include "Adj Close" — keep it but ensure
        # the canonical OHLCV columns exist.
        required = {"Open", "High", "Low", "Close", "Volume"}
        if not required.issubset(history.columns):
            return None

        # Yahoo info dict can be flaky: protect against missing fields.
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        return TickerData(symbol=symbol, history=history, info=info)

    except Exception as exc:  # noqa: BLE001 — surface to UI as None
        # Streamlit logs are visible in the terminal — leave a breadcrumb.
        st.write(f"⚠️ Data fetch error for {symbol}: {exc}")
        return None


def get_friendly_name(data: TickerData) -> str:
    """Return a human-readable label, falling back to the ticker."""
    info = data.info or {}
    return info.get("longName") or info.get("shortName") or data.symbol
