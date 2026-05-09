"""
main_view.py
=============

Główny widok aplikacji — orchestrator stron.

Sidebar steruje wyborem strony:
  • Analiza pojedynczej spółki  (rozszerzona — z LLM, BB/VWAP, PDF)
  • Skaner rynku
  • Porównywarka spółek

Każda strona to osobna funkcja `render_*_page()`, dla łatwiejszej
nawigacji w kodzie.
"""

from __future__ import annotations

import streamlit as st

from app.core.ai_analyst import AnalysisReport, analyze
from app.core.chart_builder import build_chart, build_compare_chart
from app.core.data_fetcher import fetch_ticker, get_friendly_name
from app.core.indicators import compute_all
from app.core.indicators_extra import append_extras
from app.i18n import strings_pl as t
from app.services import llm_analyst
from app.services.alerts import (
    AlertCriteria,
    format_alert_email_html,
    format_alert_message,
    scan_and_summarize,
    send_email,
    send_telegram,
)
from app.services.pdf_export import build_pdf
from app.services.scanner import WATCHLISTS, scan_universe
from app.utils.formatters import (
    color_for_grade,
    color_for_risk,
    color_for_score,
    format_market_cap,
    format_price,
    format_volume,
    pl_momentum,
    pl_risk,
    pl_trend,
)


DEFAULT_TICKERS = ["PLTR", "NVDA", "HIMS", "SOUN", "APP", "TMDX", "TSLA", "META"]


# ===========================================================================
# Konfiguracja strony + CSS
# ===========================================================================

def _configure_page() -> None:
    st.set_page_config(
        page_title="Skaner Momentum",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
        .main > div { padding-top: 1rem; }
        .stMetric { background: #1a1f2e; border-radius: 10px;
                    padding: 12px 16px; border: 1px solid #2a3042; }
        .bull-item { padding: 8px 12px; border-radius: 6px;
                     background: rgba(38,166,154,0.12);
                     border-left: 3px solid #26a69a;
                     margin-bottom: 6px; color: #d4e9e6; font-size: 0.92rem; }
        .bear-item { padding: 8px 12px; border-radius: 6px;
                     background: rgba(239,83,80,0.12);
                     border-left: 3px solid #ef5350;
                     margin-bottom: 6px; color: #f0d4d4; font-size: 0.92rem; }
        .narrative { font-size: 0.95rem; line-height: 1.55;
                     color: #d0d4dc; padding: 4px 0; }
        .badge-big { display: inline-block; font-size: 2.2rem;
                     font-weight: 700; padding: 6px 18px;
                     border-radius: 12px; color: white; min-width: 90px;
                     text-align: center; }
        h2, h3 { color: #e8eaed; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] {
            background: #1a1f2e; border-radius: 6px 6px 0 0; padding: 6px 16px;
        }
        .llm-box { background: #1a1f2e; border: 1px solid #2a3042;
                   border-left: 4px solid #7c4dff;
                   border-radius: 8px; padding: 16px 20px;
                   margin: 8px 0; line-height: 1.6; color: #d0d4dc; }
    </style>
    """, unsafe_allow_html=True)


# ===========================================================================
# Sidebar — nawigacja + ustawienia
# ===========================================================================

def _render_sidebar() -> dict:
    with st.sidebar:
        st.markdown(f"## 📈 {t.APP_TITLE}")
        st.caption(t.APP_SUBTITLE)

        page = st.radio(
            "Nawigacja",
            options=[t.NAV_ANALYSIS, t.NAV_SCANNER, t.NAV_COMPARE],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown(f"### {t.SIDEBAR_SETTINGS}")

        # Pole tickera (używane na stronie analizy)
        ticker = st.text_input(
            t.SIDEBAR_TICKER,
            value=st.session_state.get("ticker", "NVDA"),
            help=t.SIDEBAR_TICKER_HELP,
        ).strip().upper()

        period = st.selectbox(
            t.SIDEBAR_PERIOD,
            options=list(t.PERIOD_LABELS.keys()),
            index=1,
            format_func=lambda k: t.PERIOD_LABELS[k],
        )

        st.markdown("---")
        st.markdown(t.SIDEBAR_QUICK)
        cols = st.columns(2)
        for i, sym in enumerate(DEFAULT_TICKERS):
            if cols[i % 2].button(sym, key=f"qp_{sym}", use_container_width=True):
                st.session_state["ticker"] = sym
                st.rerun()

        st.markdown("---")
        with st.expander(t.SIDEBAR_ABOUT):
            st.markdown(t.SIDEBAR_ABOUT_TEXT)

    return {"page": page, "ticker": ticker, "period": period}


# ===========================================================================
# STRONA 1 — Analiza pojedynczej spółki
# ===========================================================================

def render_analysis_page(ticker: str, period: str) -> None:
    if not ticker:
        st.info(t.INFO_ENTER_TICKER)
        return

    with st.spinner(t.LOADING.format(symbol=ticker)):
        data = fetch_ticker(ticker, period=period)

    if data is None:
        st.error(t.ERROR_FETCH.format(symbol=ticker))
        return

    name = get_friendly_name(data)

    # Compute
    enriched_basic = compute_all(data.history)
    enriched = append_extras(enriched_basic)
    report = analyze(data.history)

    last_close = float(data.history["Close"].iloc[-1])
    prev_close = float(data.history["Close"].iloc[-2]) if len(data.history) > 1 else last_close

    # Header
    _render_header(data.symbol, name, data.info, last_close, prev_close)
    st.markdown(" ")
    _render_score_strip(report)
    st.markdown(" ")

    # Wykres + opcje nakładek
    col_opts = st.columns([1, 1, 6])
    show_bb = col_opts[0].toggle("Bollinger Bands", value=False, key="show_bb")
    show_vwap = col_opts[1].toggle("VWAP", value=False, key="show_vwap")

    fig = build_chart(enriched, data.symbol, report.supports, report.resistances,
                      show_bbands=show_bb, show_vwap=show_vwap)
    st.plotly_chart(fig, use_container_width=True, theme=None)

    # Dodatkowe wskaźniki — kompaktowy panel ADX/OBV
    with st.expander("📐 Dodatkowe wskaźniki (ADX, OBV, BB Width)", expanded=False):
        cols = st.columns(4)
        adx_v = enriched["ADX"].dropna().iloc[-1] if "ADX" in enriched.columns else 0
        plus_di = enriched["+DI"].dropna().iloc[-1] if "+DI" in enriched.columns else 0
        minus_di = enriched["-DI"].dropna().iloc[-1] if "-DI" in enriched.columns else 0
        bb_w = enriched["BB_Width"].dropna().iloc[-1] if "BB_Width" in enriched.columns else 0

        adx_label = ("brak trendu" if adx_v < 20 else
                     "słaby trend" if adx_v < 25 else
                     "silny trend" if adx_v < 50 else "bardzo silny trend")
        di_dir = "wzrostowy" if plus_di > minus_di else "spadkowy"

        cols[0].metric("ADX (siła trendu)", f"{adx_v:.1f}", adx_label)
        cols[1].metric("+DI / -DI", f"{plus_di:.1f} / {minus_di:.1f}",
                       f"kierunek: {di_dir}")
        cols[2].metric("BB Width", f"{bb_w*100:.1f}%",
                       "wąsko" if bb_w < 0.05 else "normalnie" if bb_w < 0.12 else "szeroko")
        cols[3].metric("Trend OBV (5d)",
                       _obv_trend_label(enriched.get("OBV")))

    # Levels
    with st.expander(t.HEADER_LEVELS, expanded=False):
        _render_levels(report)

    # Komentarz
    st.markdown(t.HEADER_COMMENTARY)
    _render_narrative(report)

    # LLM (Claude)
    with st.expander("🤖 Pogłębiona analiza Claude (LLM)", expanded=False):
        if llm_analyst.is_available():
            if st.button("Wygeneruj komentarz Claude", type="primary"):
                with st.spinner("Claude analizuje setup…"):
                    text = llm_analyst.claude_commentary(data.symbol, report)
                st.markdown(f"<div class='llm-box'>{text}</div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(llm_analyst.claude_commentary(data.symbol, report))

    # Sygnały
    st.markdown(t.HEADER_FINAL)
    _render_signals(report)

    # Eksport PDF
    st.markdown("---")
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("📄 Generuj raport PDF", use_container_width=True):
            with st.spinner("Tworzenie PDF…"):
                pdf_bytes = build_pdf(data.symbol, name, report)
            st.session_state[f"pdf_{ticker}"] = pdf_bytes
        if f"pdf_{ticker}" in st.session_state:
            st.download_button(
                "⬇️ Pobierz PDF",
                data=st.session_state[f"pdf_{ticker}"],
                file_name=f"raport_{ticker}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.caption(t.FOOTER_DISCLAIMER)


def _obv_trend_label(obv_series) -> str:
    """5-dniowa zmiana OBV jako etykieta kierunku."""
    if obv_series is None or len(obv_series.dropna()) < 6:
        return "—"
    s = obv_series.dropna()
    change = (s.iloc[-1] - s.iloc[-6]) / abs(s.iloc[-6]) * 100 if s.iloc[-6] else 0
    if change > 5:   return f"↑ rośnie ({change:+.1f}%)"
    if change < -5:  return f"↓ spada ({change:+.1f}%)"
    return f"→ płaski ({change:+.1f}%)"


# ===========================================================================
# STRONA 2 — Skaner rynku
# ===========================================================================

def render_scanner_page(period: str) -> None:
    st.markdown(f"# {t.NAV_SCANNER}")
    st.caption("Przeskanuj predefiniowane uniwersum lub własną listę i znajdź "
               "spółki z najlepszymi setupami momentum.")

    cols = st.columns([2, 2, 1])
    universe_name = cols[0].selectbox(
        "Wybierz uniwersum",
        options=list(WATCHLISTS.keys()) + ["Własna lista (wpisz poniżej)"],
    )
    custom_input = ""
    if universe_name == "Własna lista (wpisz poniżej)":
        custom_input = cols[1].text_input(
            "Tickery (rozdzielone przecinkami)",
            placeholder="NVDA, PLTR, HIMS, SOUN, APP",
        )
        symbols = [s.strip().upper() for s in custom_input.split(",") if s.strip()]
    else:
        symbols = WATCHLISTS[universe_name]
        cols[1].info(f"Uniwersum: **{len(symbols)}** spółek")

    run = cols[2].button("🔍 Skanuj", type="primary", use_container_width=True)

    if run and symbols:
        progress = st.progress(0.0, text="Skanowanie…")
        status = st.empty()

        def cb(done: int, total: int):
            progress.progress(done / total,
                              text=f"Przeanalizowano {done}/{total}…")

        df = scan_universe(symbols, period=period, progress_cb=cb)
        progress.empty()
        status.empty()

        if df.empty:
            st.warning("Skaner nie zwrócił wyników.")
            return

        st.session_state["scan_df"] = df
        st.session_state["scan_universe"] = universe_name

    # Wyświetl ostatni wynik (jeśli jest)
    if "scan_df" in st.session_state:
        df = st.session_state["scan_df"]
        st.markdown(f"### Wyniki skanu — {st.session_state.get('scan_universe', '')}")

        # Filtry
        col_f = st.columns(4)
        min_score = col_f[0].slider("Min. ocena", 1.0, 10.0, 5.0, 0.5)
        max_risk = col_f[1].selectbox("Max. ryzyko",
                                      ["Low", "Medium", "High", "Extreme"], index=2)
        risk_order = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
        view = df[(df["score"] >= min_score)
                  & (df["risk"].map(lambda r: risk_order.get(r, 99)) <= risk_order[max_risk])].copy()

        view["risk_pl"] = view["risk"].map(pl_risk)
        view["trend_pl"] = view["trend"].map(pl_trend)
        view["momentum_pl"] = view["momentum"].map(pl_momentum)

        display = view[["symbol", "score", "setup", "risk_pl",
                        "trend_pl", "momentum_pl",
                        "last_close", "n_bull", "n_bear"]].rename(columns={
            "symbol": "Symbol", "score": "Ocena", "setup": "Setup",
            "risk_pl": "Ryzyko", "trend_pl": "Trend",
            "momentum_pl": "Momentum",
            "last_close": "Cena", "n_bull": "✅", "n_bear": "⚠️",
        })

        st.dataframe(
            display, use_container_width=True, hide_index=True,
            column_config={
                "Ocena": st.column_config.ProgressColumn(
                    "Ocena", min_value=1, max_value=10, format="%.1f"),
                "Cena": st.column_config.NumberColumn("Cena", format="$%.2f"),
            },
        )

        st.caption(f"Pokazano {len(view)}/{len(df)} spółek po filtrach. "
                   f"Kliknij ticker w panelu bocznym i wróć do strony 'Analiza' "
                   f"by zobaczyć szczegóły.")

        # Sekcja alertów
        with st.expander("🔔 Wyślij alerty dla najlepszych setupów"):
            ac1, ac2, ac3 = st.columns(3)
            min_alert_score = ac1.slider("Min. ocena alertu", 5.0, 10.0, 8.0, 0.5)
            min_alert_bull = ac2.slider("Min. sygnałów byczych", 1, 8, 3)
            max_alert_risk = ac3.selectbox("Max. ryzyko alertu",
                                           ["Low", "Medium", "High"], index=1)

            criteria = AlertCriteria(
                min_score=min_alert_score,
                min_bull_signals=min_alert_bull,
                max_risk=max_alert_risk,
            )
            alerts_df = scan_and_summarize(df, criteria)

            if alerts_df.empty:
                st.info("Brak spółek spełniających kryteria alertu.")
            else:
                st.success(f"**{len(alerts_df)}** spółek spełnia kryteria:")
                st.dataframe(
                    alerts_df[["symbol", "score", "setup", "risk", "n_bull"]],
                    hide_index=True, use_container_width=True,
                )

                send_cols = st.columns(2)
                if send_cols[0].button("📧 Wyślij e-mail", use_container_width=True):
                    _send_alerts_email(alerts_df, period)
                if send_cols[1].button("📱 Wyślij Telegram", use_container_width=True):
                    _send_alerts_telegram(alerts_df, period)


def _send_alerts_email(alerts_df, period: str):
    """Wysyła zbiorczy e-mail z alertami."""
    rows = "".join(
        f"<tr><td><b>{r.symbol}</b></td>"
        f"<td>{r.score:.1f}/10</td><td>{r.setup}</td>"
        f"<td>{pl_risk(r.risk)}</td><td>${r.last_close:.2f}</td></tr>"
        for r in alerts_df.itertuples()
    )
    body = f"""<html><body style="font-family:system-ui">
    <h2>🚨 Alerty momentum ({len(alerts_df)} spółek)</h2>
    <table border=1 cellpadding=6 style="border-collapse:collapse">
    <tr style="background:#1f2a44;color:white">
    <th>Symbol</th><th>Ocena</th><th>Setup</th><th>Ryzyko</th><th>Cena</th>
    </tr>{rows}</table>
    <p style="color:#888;font-size:0.85rem">Skaner Momentum — analiza edukacyjna.</p>
    </body></html>"""
    ok, msg = send_email(f"🚨 Alert momentum — {len(alerts_df)} spółek", body)
    (st.success if ok else st.error)(msg)


def _send_alerts_telegram(alerts_df, period: str):
    """Wysyła zbiorczą wiadomość Telegram."""
    lines = "\n".join(
        f"• *{r.symbol}* — {r.score:.1f}/10 ({r.setup}) • {pl_risk(r.risk)}"
        for r in alerts_df.itertuples()
    )
    text = f"🚨 *Alerty momentum* ({len(alerts_df)} spółek):\n\n{lines}"
    ok, msg = send_telegram(text)
    (st.success if ok else st.error)(msg)


# ===========================================================================
# STRONA 3 — Porównywarka
# ===========================================================================

def render_compare_page(period: str) -> None:
    st.markdown(f"# {t.NAV_COMPARE}")
    st.caption("Porównaj 2-3 spółki obok siebie.")

    cols = st.columns(3)
    sym1 = cols[0].text_input("Spółka 1", value="NVDA").strip().upper()
    sym2 = cols[1].text_input("Spółka 2", value="PLTR").strip().upper()
    sym3 = cols[2].text_input("Spółka 3 (opcjonalnie)", value="").strip().upper()

    syms = [s for s in [sym1, sym2, sym3] if s]
    if len(syms) < 2:
        st.info("Wpisz co najmniej dwa tickery powyżej.")
        return

    if not st.button("⚖️ Porównaj", type="primary"):
        return

    results = {}
    dfs_for_chart = {}
    with st.spinner("Pobieranie i analiza…"):
        for s in syms:
            data = fetch_ticker(s, period=period)
            if data is None:
                st.error(f"Brak danych dla {s}")
                continue
            results[s] = (data, analyze(data.history))
            dfs_for_chart[s] = data.history

    if not results:
        return

    # Wykres znormalizowanych zwrotów
    st.plotly_chart(build_compare_chart(dfs_for_chart),
                    use_container_width=True, theme=None)

    # Tabela porównawcza
    rows = []
    for sym, (data, rep) in results.items():
        rows.append({
            "Symbol": sym,
            "Cena": format_price(rep.last_close),
            "Ocena": f"{rep.technical_score:.1f}/10",
            "Setup": rep.setup_quality,
            "Ryzyko": pl_risk(rep.risk_level),
            "Trend": pl_trend(rep.trend_label),
            "Momentum": pl_momentum(rep.momentum_rating),
            "Sygnały ✅": len(rep.bullish_signals),
            "Sygnały ⚠️": len(rep.bearish_signals),
        })
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # Mini-narracje obok siebie
    st.markdown("### Krótka teza dla każdej spółki")
    cols = st.columns(len(results))
    for col, (sym, (_, rep)) in zip(cols, results.items()):
        with col:
            st.markdown(f"**{sym}** — {rep.setup_quality} / {rep.technical_score:.1f}")
            st.markdown(f"<div class='narrative'>{rep.health_assessment}</div>",
                        unsafe_allow_html=True)


# ===========================================================================
# Komponenty wspólne
# ===========================================================================

def _render_header(symbol, name, info, last, prev) -> None:
    change = last - prev
    pct = (change / prev * 100) if prev else 0
    arrow = "▲" if change >= 0 else "▼"
    color = "#26a69a" if change >= 0 else "#ef5350"

    st.markdown(
        f"<h1 style='margin-bottom:0'>{symbol} "
        f"<span style='font-size:1rem;color:#9e9e9e;font-weight:400'>"
        f"— {name}</span></h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:1.8rem;font-weight:600'>"
        f"{format_price(last)} "
        f"<span style='font-size:1.1rem;color:{color}'>"
        f"{arrow} {format_price(abs(change))} ({pct:+.2f}%)</span></div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    cols[0].metric(t.METRIC_SECTOR, info.get("sector", "—"))
    cols[1].metric(t.METRIC_INDUSTRY, (info.get("industry") or "—")[:25])
    cols[2].metric(t.METRIC_MARKET_CAP, format_market_cap(info.get("marketCap")))
    cols[3].metric(t.METRIC_AVG_VOLUME, format_volume(info.get("averageVolume")))


def _render_score_strip(report: AnalysisReport) -> None:
    cols = st.columns([1.2, 1, 1, 1, 1])

    with cols[0]:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='color:#9e9e9e;font-size:0.85rem;margin-bottom:6px'>"
            f"{t.LABEL_TECH_SCORE}</div>"
            f"<span class='badge-big' style='background:{color_for_score(report.technical_score)}'>"
            f"{report.technical_score:.1f}</span>"
            f"<div style='color:#9e9e9e;font-size:0.75rem;margin-top:4px'>{t.LABEL_OUT_OF}</div>"
            f"</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='color:#9e9e9e;font-size:0.85rem;margin-bottom:6px'>"
            f"{t.LABEL_SETUP}</div>"
            f"<span class='badge-big' style='background:{color_for_grade(report.setup_quality)}'>"
            f"{report.setup_quality}</span>"
            f"</div>", unsafe_allow_html=True)

    with cols[2]:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='color:#9e9e9e;font-size:0.85rem;margin-bottom:6px'>"
            f"{t.LABEL_RISK}</div>"
            f"<span class='badge-big' style='background:{color_for_risk(report.risk_level)};font-size:1.4rem;line-height:2.2'>"
            f"{pl_risk(report.risk_level)}</span>"
            f"</div>", unsafe_allow_html=True)

    with cols[3]:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='color:#9e9e9e;font-size:0.85rem;margin-bottom:6px'>"
            f"{t.LABEL_MOMENTUM}</div>"
            f"<span class='badge-big' style='background:#3949ab;font-size:1.3rem;line-height:2.4'>"
            f"{pl_momentum(report.momentum_rating)}</span>"
            f"</div>", unsafe_allow_html=True)

    with cols[4]:
        st.markdown(
            f"<div style='text-align:center'>"
            f"<div style='color:#9e9e9e;font-size:0.85rem;margin-bottom:6px'>"
            f"{t.LABEL_TREND}</div>"
            f"<span class='badge-big' style='background:#5e35b1;font-size:1.05rem;line-height:2.8'>"
            f"{pl_trend(report.trend_label)}</span>"
            f"</div>", unsafe_allow_html=True)


def _render_narrative(report: AnalysisReport) -> None:
    tabs = st.tabs([
        t.TAB_TREND, t.TAB_MOMENTUM, t.TAB_INSTITUTIONAL,
        t.TAB_EXTENSION, t.TAB_VOLUME, t.TAB_HEALTH,
    ])
    pieces = [
        report.trend_direction,
        report.momentum_quality,
        report.institutional_read,
        report.extension_read,
        report.volume_confirmation,
        report.health_assessment,
    ]
    for tab, text in zip(tabs, pieces):
        with tab:
            st.markdown(f"<div class='narrative'>{text}</div>",
                        unsafe_allow_html=True)


def _render_signals(report: AnalysisReport) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(t.HEADER_BULLISH)
        if report.bullish_signals:
            for s in report.bullish_signals:
                st.markdown(f"<div class='bull-item'>• {s}</div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='narrative' style='color:#9e9e9e'>"
                        f"{t.NO_BULL_SIGNALS}</div>",
                        unsafe_allow_html=True)
    with col2:
        st.markdown(t.HEADER_BEARISH)
        if report.bearish_signals:
            for s in report.bearish_signals:
                st.markdown(f"<div class='bear-item'>• {s}</div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='narrative' style='color:#9e9e9e'>"
                        f"{t.NO_BEAR_SIGNALS}</div>",
                        unsafe_allow_html=True)


def _render_levels(report: AnalysisReport) -> None:
    if not report.supports and not report.resistances:
        return
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(t.LEVEL_SUPPORTS)
        for s in report.supports:
            pct = (s / report.last_close - 1) * 100
            st.markdown(f"- {format_price(s)} (_{pct:.1f}% {t.LEVEL_FROM_PRICE}_)")
        if not report.supports:
            st.markdown(t.LEVEL_NONE)
    with col2:
        st.markdown(t.LEVEL_RESISTANCES)
        for r in report.resistances:
            pct = (r / report.last_close - 1) * 100
            st.markdown(f"- {format_price(r)} (_{pct:+.1f}% {t.LEVEL_FROM_PRICE}_)")
        if not report.resistances:
            st.markdown(t.LEVEL_NONE)


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def render_app() -> None:
    _configure_page()
    state = _render_sidebar()

    if state["page"] == t.NAV_ANALYSIS:
        render_analysis_page(state["ticker"], state["period"])
    elif state["page"] == t.NAV_SCANNER:
        render_scanner_page(state["period"])
    elif state["page"] == t.NAV_COMPARE:
        render_compare_page(state["period"])
