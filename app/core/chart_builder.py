"""
chart_builder.py
=================

4-panelowy wykres Plotly z opcjonalnymi nakładkami z extra wskaźników:

  Panel 1: Świece + EMA20/50/200 + (opcj.) Bollinger Bands + (opcj.) VWAP + S/R
  Panel 2: Wolumen + 20 MA wolumenu
  Panel 3: RSI + MA9/MA21 RSI
  Panel 4: MACD line + signal + histogram

Tytuły osi i legend są po polsku.
"""

from __future__ import annotations

from typing import List

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Paleta dopasowana do dark mode
COLOR_UP = "#26a69a"
COLOR_DOWN = "#ef5350"
COLOR_EMA20 = "#42a5f5"
COLOR_EMA50 = "#ffb300"
COLOR_EMA200 = "#ab47bc"
COLOR_RSI = "#e0e0e0"
COLOR_RSI_FAST = "#42a5f5"
COLOR_RSI_SLOW = "#ffb300"
COLOR_VOL_AVG = "#9e9e9e"
COLOR_MACD = "#42a5f5"
COLOR_SIGNAL = "#ffb300"
COLOR_BB = "rgba(120, 144, 156, 0.5)"
COLOR_BB_FILL = "rgba(120, 144, 156, 0.08)"
COLOR_VWAP = "#80deea"


def build_chart(df: pd.DataFrame, symbol: str,
                supports: List[float], resistances: List[float],
                show_bbands: bool = False,
                show_vwap: bool = False) -> go.Figure:
    """
    Buduje 4-panelowy wykres analizy.

    `df` musi mieć kolumny z indicators.compute_all() — opcjonalnie BB_*/VWAP
    dorzucone przez indicators_extra.append_extras().
    """

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.50, 0.15, 0.18, 0.17],
        subplot_titles=(
            f"{symbol} — Cena z EMA i poziomami",
            "Wolumen",
            "RSI (14) z MA 9/21",
            "MACD (12, 26, 9)",
        ),
    )

    # --- Panel 1 — świece + EMA + (BB/VWAP) + S/R ---
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Cena",
        increasing_line_color=COLOR_UP, decreasing_line_color=COLOR_DOWN,
        showlegend=False,
    ), row=1, col=1)

    # Bollinger Bands (opcjonalne)
    if show_bbands and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"], name="BB górne",
            line=dict(color=COLOR_BB, width=1, dash="dot"),
            hovertemplate="BB górne: %{y:.2f}<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"], name="BB dolne",
            line=dict(color=COLOR_BB, width=1, dash="dot"),
            fill="tonexty", fillcolor=COLOR_BB_FILL,
            hovertemplate="BB dolne: %{y:.2f}<extra></extra>",
        ), row=1, col=1)

    # VWAP (opcjonalny)
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"], name="VWAP",
            line=dict(color=COLOR_VWAP, width=1.4, dash="dash"),
            hovertemplate="VWAP: %{y:.2f}<extra></extra>",
        ), row=1, col=1)

    # EMA
    for col, color, width in [("EMA20", COLOR_EMA20, 1.4),
                              ("EMA50", COLOR_EMA50, 1.6),
                              ("EMA200", COLOR_EMA200, 1.8)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=col,
                line=dict(color=color, width=width),
                hovertemplate=f"{col}: %{{y:.2f}}<extra></extra>",
            ), row=1, col=1)

    # S/R
    for level in resistances:
        fig.add_hline(y=level, line_dash="dash", line_width=1,
                      line_color="rgba(239, 83, 80, 0.55)",
                      row=1, col=1,  # type: ignore[arg-type]
                      annotation_text=f"O {level:.2f}",
                      annotation_position="right",
                      annotation_font_color="rgba(239, 83, 80, 0.9)")
    for level in supports:
        fig.add_hline(y=level, line_dash="dash", line_width=1,
                      line_color="rgba(38, 166, 154, 0.55)",
                      row=1, col=1,  # type: ignore[arg-type]
                      annotation_text=f"W {level:.2f}",
                      annotation_position="right",
                      annotation_font_color="rgba(38, 166, 154, 0.9)")

    # --- Panel 2 — wolumen ---
    vol_colors = [COLOR_UP if c >= o else COLOR_DOWN
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="Wolumen",
        marker_color=vol_colors, opacity=0.7, showlegend=False,
        hovertemplate="Wol: %{y:,.0f}<extra></extra>",
    ), row=2, col=1)
    vol_avg = df["Volume"].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=vol_avg, name="MA20 wol.",
        line=dict(color=COLOR_VOL_AVG, width=1.2, dash="dot"),
        hovertemplate="MA20 wol.: %{y:,.0f}<extra></extra>",
    ), row=2, col=1)

    # --- Panel 3 — RSI ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"], name="RSI",
        line=dict(color=COLOR_RSI, width=1.6),
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI_MA9"], name="RSI MA9",
        line=dict(color=COLOR_RSI_FAST, width=1.0),
        hovertemplate="RSI MA9: %{y:.1f}<extra></extra>",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI_MA21"], name="RSI MA21",
        line=dict(color=COLOR_RSI_SLOW, width=1.0),
        hovertemplate="RSI MA21: %{y:.1f}<extra></extra>",
    ), row=3, col=1)
    for y, dash, alpha in [(70, "dash", 0.4), (50, "dot", 0.25), (30, "dash", 0.4)]:
        fig.add_hline(y=y, line_dash=dash,
                      line_color=f"rgba(180,180,180,{alpha})",
                      line_width=1, row=3, col=1)  # type: ignore[arg-type]

    # --- Panel 4 — MACD ---
    hist_colors = [COLOR_UP if v >= 0 else COLOR_DOWN
                   for v in df["MACD_Hist"].fillna(0)]
    fig.add_trace(go.Bar(
        x=df.index, y=df["MACD_Hist"], name="Histogram",
        marker_color=hist_colors, opacity=0.55, showlegend=False,
        hovertemplate="Hist: %{y:.3f}<extra></extra>",
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD"], name="MACD",
        line=dict(color=COLOR_MACD, width=1.4),
        hovertemplate="MACD: %{y:.3f}<extra></extra>",
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD_Signal"], name="Sygnał",
        line=dict(color=COLOR_SIGNAL, width=1.2),
        hovertemplate="Sygnał: %{y:.3f}<extra></extra>",
    ), row=4, col=1)

    # Layout
    fig.update_layout(
        template="plotly_dark", height=820,
        margin=dict(l=10, r=80, t=50, b=20),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#e0e0e0", size=11),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    return fig


def build_compare_chart(symbols_dfs: dict[str, pd.DataFrame]) -> go.Figure:
    """
    Wykres porównawczy: znormalizowany zwrot procentowy od pierwszego dnia
    dla 2-3 spółek na jednym panelu. Liczone jako (Close / Close[0] - 1) * 100.
    """
    fig = go.Figure()
    palette = ["#42a5f5", "#26a69a", "#ffb300", "#ab47bc"]
    for i, (sym, df) in enumerate(symbols_dfs.items()):
        if df.empty:
            continue
        norm = (df["Close"] / df["Close"].iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=norm, name=sym,
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"{sym}: %{{y:.2f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(180,180,180,0.4)")
    fig.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=10, r=20, t=40, b=20),
        title="Znormalizowany zwrot (% od początku okresu)",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#e0e0e0", size=11),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                     ticksuffix="%")
    return fig
