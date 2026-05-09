"""
alerts.py
==========

Lekki system alertów. Dwa kanały:

1. **E-mail** przez SMTP (np. Gmail z hasłem aplikacji).
2. **Telegram** przez Bot API.

Konfiguracja przez .streamlit/secrets.toml lub zmienne środowiskowe:

    [secrets]                         (lub odpowiednie env-var)
    SMTP_HOST = "smtp.gmail.com"      SMTP_HOST
    SMTP_PORT = 587                   SMTP_PORT
    SMTP_USER = "ja@gmail.com"        SMTP_USER
    SMTP_PASS = "haslo-aplikacji"     SMTP_PASS
    ALERT_EMAIL_TO = "ja@gmail.com"   ALERT_EMAIL_TO

    TELEGRAM_BOT_TOKEN = "12345:..."  TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = "123456789"    TELEGRAM_CHAT_ID

`alert_runner.py` zawiera pętlę do okresowego skanowania i wysyłki.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import pandas as pd

from app.core.ai_analyst import AnalysisReport


def _cfg(key: str, default=None):
    """Czyta z env, fallback na st.secrets."""
    val = os.environ.get(key)
    if val is not None:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)  # type: ignore[attr-defined]
    except Exception:
        return default


# ---------------------------------------------------------------------------
# E-mail
# ---------------------------------------------------------------------------

def send_email(subject: str, body_html: str,
               to: Optional[str] = None) -> tuple[bool, str]:
    """Wysyła HTML-mail. Zwraca (ok, komunikat)."""
    host = _cfg("SMTP_HOST")
    port = int(_cfg("SMTP_PORT", 587))
    user = _cfg("SMTP_USER")
    pwd = _cfg("SMTP_PASS")
    to = to or _cfg("ALERT_EMAIL_TO") or user
    if not all([host, user, pwd, to]):
        return False, ("Brak konfiguracji SMTP. Ustaw SMTP_HOST/USER/PASS "
                       "i ALERT_EMAIL_TO w secrets.toml.")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port) as srv:
            srv.starttls(context=ctx)
            srv.login(user, pwd)
            srv.sendmail(user, [to], msg.as_string())
        return True, f"Wysłano e-mail do {to}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Błąd SMTP: {exc}"


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(text: str) -> tuple[bool, str]:
    """Wysyła wiadomość Markdown przez Bot API. (ok, komunikat)."""
    token = _cfg("TELEGRAM_BOT_TOKEN")
    chat_id = _cfg("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        return False, ("Brak konfiguracji Telegrama. Ustaw "
                       "TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID.")
    try:
        import requests  # standardowo z yfinance
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        if r.ok:
            return True, "Wysłano na Telegram"
        return False, f"Telegram API: HTTP {r.status_code} — {r.text[:120]}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Błąd Telegrama: {exc}"


# ---------------------------------------------------------------------------
# Formatowanie powiadomień
# ---------------------------------------------------------------------------

@dataclass
class AlertCriteria:
    """Reguły decydujące, czy spółka warta alertu."""
    min_score: float = 8.0           # tylko score >= 8
    min_bull_signals: int = 3        # min 3 sygnały bycze
    max_risk: str = "Medium"         # nie alarmuj o "High"/"Extreme"
    require_breakout: bool = False   # tylko świeże wybicia

    def matches(self, score: float, n_bull: int, risk: str,
                signals: list[str]) -> bool:
        risk_order = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
        if score < self.min_score:
            return False
        if n_bull < self.min_bull_signals:
            return False
        if risk_order.get(risk, 99) > risk_order.get(self.max_risk, 1):
            return False
        if self.require_breakout and not any("Wybicie" in s for s in signals):
            return False
        return True


def format_alert_message(symbol: str, report: AnalysisReport) -> str:
    """Markdown-friendly wiadomość alertowa (do Telegrama / e-maila)."""
    bullets = "\n".join(f"  ✅ {s}" for s in report.bullish_signals[:5])
    return (
        f"🚨 *ALERT MOMENTUM: {symbol}*\n\n"
        f"📊 Ocena: *{report.technical_score:.1f}/10*  |  "
        f"Setup: *{report.setup_quality}*  |  Ryzyko: {report.risk_level}\n"
        f"📈 Trend: {report.trend_label}\n"
        f"⚡ Momentum: {report.momentum_rating}\n"
        f"💵 Cena: ${report.last_close:.2f}\n\n"
        f"*Sygnały pozytywne:*\n{bullets}\n"
    )


def format_alert_email_html(symbol: str, report: AnalysisReport) -> str:
    """HTML wersja powiadomienia."""
    bullets = "".join(f"<li>{s}</li>" for s in report.bullish_signals)
    return f"""
    <html><body style="font-family:system-ui,sans-serif;color:#222">
    <h2>🚨 Alert momentum: {symbol}</h2>
    <p style="font-size:1.1rem">
        <b>Ocena techniczna:</b> {report.technical_score:.1f}/10 &nbsp;
        <b>Setup:</b> {report.setup_quality} &nbsp;
        <b>Ryzyko:</b> {report.risk_level}
    </p>
    <p>
        <b>Trend:</b> {report.trend_label}<br>
        <b>Momentum:</b> {report.momentum_rating}<br>
        <b>Cena:</b> ${report.last_close:.2f}
    </p>
    <h3 style="color:#26a69a">Sygnały pozytywne</h3>
    <ul>{bullets}</ul>
    <p style="font-size:0.85rem;color:#888">
        Wygenerowano przez Skaner Momentum. Nie stanowi rekomendacji inwestycyjnej.
    </p>
    </body></html>
    """


def scan_and_summarize(scan_df: pd.DataFrame,
                       criteria: AlertCriteria) -> pd.DataFrame:
    """Filtruje wyniki skanera do tych spełniających kryteria alertu."""
    if scan_df.empty:
        return scan_df
    risk_order = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
    df = scan_df.copy()
    df["risk_rank"] = df["risk"].map(lambda r: risk_order.get(r, 99))
    mask = (
        (df["score"] >= criteria.min_score)
        & (df["n_bull"] >= criteria.min_bull_signals)
        & (df["risk_rank"] <= risk_order.get(criteria.max_risk, 1))
    )
    return df[mask].drop(columns=["risk_rank"]).reset_index(drop=True)
