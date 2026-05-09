"""
llm_analyst.py
===============

Integracja z Claude API — opcjonalne, pogłębione komentarze po polsku.
Bierze deterministyczny AnalysisReport jako kontekst (LLM nie generuje
liczb, tylko narrację), żeby zminimalizować ryzyko halucynacji.
"""

from __future__ import annotations

import os
from typing import Optional

from app.core.ai_analyst import AnalysisReport


DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")

SYSTEM_PROMPT = """Jesteś zdyscyplinowanym analitykiem akcji w stylu inwestowania
momentum (szkoła Minerviniego/O'Neila/Wyckoffa). Piszesz po polsku,
profesjonalnym, suchym tonem — jak notatka z funduszu, nie jak influencer.

ZASADY:
1. Mów w kategoriach prawdopodobieństwa, nigdy pewności. Unikaj słów typu
   "na pewno", "wystrzeli", "moonshot", "guaranteed".
2. Priorytety: jakość trendu, potwierdzenie wolumenowe, akumulacja
   instytucjonalna, struktura RSI, struktura średnich kroczących.
3. Setup rozciągnięty (>6 ATR nad EMA50) zawsze obniża ocenę nawet przy
   silnym trendzie — chasing szczytów to słaba statystyka.
4. Nie wymyślaj danych. Jeśli czegoś nie wiesz — powiedz to wprost.
5. Krótko: 3-4 akapity, łącznie ~250-350 słów.
6. NIE jest to rekomendacja inwestycyjna — pisz analitycznie, nie nakazowo.

STRUKTURA ODPOWIEDZI:
- Akapit 1: ogólna teza setupu (czy jest tradeable, na jakim etapie)
- Akapit 2: co potwierdza / co podważa, ze szczególnym uwzględnieniem wolumenu
- Akapit 3: kluczowe poziomy techniczne i co by wywróciło tezę (invalidation)
- Akapit 4 (opcjonalny): co obserwować w najbliższych sesjach
"""


def _build_user_prompt(symbol: str, report: AnalysisReport) -> str:
    bullish = "\n".join(f"- {s}" for s in report.bullish_signals) or "(brak)"
    bearish = "\n".join(f"- {s}" for s in report.bearish_signals) or "(brak)"
    supports = ", ".join(f"${s:.2f}" for s in report.supports) or "(brak)"
    resistances = ", ".join(f"${r:.2f}" for r in report.resistances) or "(brak)"

    return f"""Przeanalizuj setup techniczny dla **{symbol}**.

Dane z silnika regułowego (źródło prawdy — nie kwestionuj liczb):

OCENA OGÓLNA:
- Ocena techniczna: {report.technical_score}/10
- Jakość setupu: {report.setup_quality}
- Poziom ryzyka: {report.risk_level}
- Momentum: {report.momentum_rating}
- Trend: {report.trend_label}
- Aktualna cena: ${report.last_close:.2f}

NARRACJA SKŁADOWYCH:
- TREND: {report.trend_direction}
- MOMENTUM: {report.momentum_quality}
- INSTYTUCJE: {report.institutional_read}
- ROZCIĄGNIĘCIE: {report.extension_read}
- WOLUMEN: {report.volume_confirmation}
- ZDROWIE SETUPU: {report.health_assessment}

SYGNAŁY POZYTYWNE:
{bullish}

SYGNAŁY NEGATYWNE:
{bearish}

POZIOMY:
- Wsparcia: {supports}
- Opory: {resistances}

Napisz spójny komentarz (3-4 akapity) trzymając się reguł z system promptu.
"""


def _get_api_key() -> Optional[str]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        return None


def is_available() -> bool:
    """Czy LLM jest gotowe (klucz + pakiet)?"""
    if _get_api_key() is None:
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def claude_commentary(symbol: str, report: AnalysisReport,
                      model: str = DEFAULT_MODEL,
                      max_tokens: int = 900) -> str:
    """Zwraca pogłębiony komentarz Claude lub komunikat o niedostępności."""
    api_key = _get_api_key()
    if api_key is None:
        return ("ℹ️ **Pogłębiona analiza Claude niedostępna.**\n\n"
                "Aby ją włączyć, ustaw klucz API w jeden z poniższych sposobów:\n\n"
                "**Opcja 1 — zmienna środowiskowa:**\n"
                "```bash\nexport ANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
                "**Opcja 2 — plik `.streamlit/secrets.toml`:**\n"
                "```toml\nANTHROPIC_API_KEY = \"sk-ant-...\"\n```\n\n"
                "Klucz wygenerujesz na **console.anthropic.com**.")

    try:
        import anthropic
    except ImportError:
        return ("ℹ️ Pakiet `anthropic` nie jest zainstalowany. Uruchom:\n\n"
                "```bash\npip install anthropic\n```")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(symbol, report)}],
        )
        for block in message.content:
            if hasattr(block, "text"):
                return block.text
        return "(brak treści w odpowiedzi)"
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Błąd wywołania Claude API: {exc}"
