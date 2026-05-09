"""
scanner.py
===========

Skaner rynku — bierze listę tickerów, dla każdego pobiera dane, puszcza
przez `analyze()` i zwraca posortowaną tabelę kandydatów.
Wątki dla IO-bound yfinance.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from app.core.ai_analyst import analyze
from app.core.data_fetcher import fetch_ticker


# Predefiniowane uniwersa do skanowania
WATCHLISTS = {
    "Mega-cap tech (FAANG+)":
        ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO"],
    "AI / Półprzewodniki":
        ["NVDA", "AMD", "AVGO", "TSM", "MU", "AMAT", "LRCX", "KLAC",
         "CRDO", "AEHR", "CAMT", "AMKR", "INOD", "SOUN"],
    "Momentum 2025/26 (popularne)":
        ["PLTR", "NVDA", "HIMS", "SOUN", "APP", "TMDX", "DUOL", "RDDT",
         "IREN", "NBIS", "CPNG", "MELI", "AEVA", "EVLV"],
    "Fintech / Płatności":
        ["V", "MA", "PYPL", "SQ", "AFRM", "SOFI", "HOOD", "COIN"],
    "Zdrowie / Biotech":
        ["LLY", "NVO", "VRTX", "REGN", "HIMS", "TMDX", "HROW"],
    "Cloud / SaaS":
        ["MSFT", "CRM", "NOW", "SNOW", "DDOG", "NET", "MDB", "CRWD", "ZS"],
}


@dataclass
class ScanResult:
    symbol: str
    score: float
    setup: str
    risk: str
    trend: str
    momentum: str
    last_close: float
    n_bull: int
    n_bear: int
    error: Optional[str] = None


def _scan_one(symbol: str, period: str = "1y") -> ScanResult:
    try:
        data = fetch_ticker(symbol, period=period)
        if data is None:
            return ScanResult(symbol, 0, "—", "—", "—", "—", 0, 0, 0,
                              error="brak danych")
        report = analyze(data.history)
        return ScanResult(
            symbol=symbol,
            score=report.technical_score,
            setup=report.setup_quality,
            risk=report.risk_level,
            trend=report.trend_label,
            momentum=report.momentum_rating,
            last_close=report.last_close,
            n_bull=len(report.bullish_signals),
            n_bear=len(report.bearish_signals),
        )
    except Exception as exc:  # noqa: BLE001
        return ScanResult(symbol, 0, "—", "—", "—", "—", 0, 0, 0,
                          error=str(exc)[:80])


def scan_universe(symbols: List[str], period: str = "1y",
                  max_workers: int = 8,
                  progress_cb=None) -> pd.DataFrame:
    """
    Skanuje listę tickerów równolegle.

    progress_cb : callable(done, total) | None — callback paska postępu.
    Returns posortowaną tabelę DESC po score, n_bull.
    """
    results: List[ScanResult] = []
    done = 0
    total = len(symbols)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_scan_one, s, period): s for s in symbols}
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if progress_cb:
                progress_cb(done, total)

    df = pd.DataFrame([r.__dict__ for r in results])
    if df.empty:
        return df
    df = df.sort_values(["score", "n_bull"], ascending=[False, False])
    return df.reset_index(drop=True)
