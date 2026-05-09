"""
pdf_export.py
==============

Eksport pełnego raportu analitycznego do pliku PDF.

Używamy `reportlab` (proste, niezawodne, działa wszędzie). Zamieniamy:
- nagłówek z tickerem i ceną
- pasek wskaźników (score / setup / risk / momentum / trend)
- 6 sekcji narracyjnych
- listy sygnałów byczych i niedźwiedzich
- poziomy S/R
- (opcjonalnie) wykres jako PNG, jeśli użytkownik dostarczy gotowy plik

Wynik jako bytes — Streamlit wystawia przez st.download_button.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Optional

from app.core.ai_analyst import AnalysisReport
from app.i18n import strings_pl as t


def build_pdf(symbol: str, name: str, report: AnalysisReport,
              chart_png_bytes: Optional[bytes] = None) -> bytes:
    """
    Generuje raport PDF i zwraca go jako bytes (gotowe do download_button).

    `chart_png_bytes` — opcjonalne, gdy mamy snapshot wykresu (z plotly
    przez kaleido). Jeśli None — PDF będzie tylko tekstowy.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image, ListFlowable, ListItem, PageBreak, Paragraph,
            SimpleDocTemplate, Spacer, Table, TableStyle,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return b"reportlab nie jest zainstalowany"

    # Polskie znaki: ReportLab natywnie obsługuje Helveticę z latin-1.
    # Dla pewności rejestrujemy DejaVu jeśli dostępne — fallback do Helvetica.
    base_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    try:
        for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                     "/Library/Fonts/Arial Unicode.ttf",
                     "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
            try:
                pdfmetrics.registerFont(TTFont("Body", path))
                base_font = "Body"
                bold_font = "Body"  # bez bolda — minimalizujemy ryzyko
                break
            except Exception:
                continue
    except Exception:
        pass

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"],
                        fontName=bold_font, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"],
                        fontName=bold_font, fontSize=12, spaceBefore=10, spaceAfter=4,
                        textColor=colors.HexColor("#1f2a44"))
    body = ParagraphStyle("body", parent=styles["BodyText"],
                          fontName=base_font, fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=styles["BodyText"],
                           fontName=base_font, fontSize=8, textColor=colors.grey)

    flow = []

    # Header
    flow.append(Paragraph(f"{symbol} — {name}", h1))
    flow.append(Paragraph(
        f"Raport analizy technicznej · wygenerowano "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}", small))
    flow.append(Spacer(1, 0.4 * cm))

    # Tabela ocen
    momentum_pl = t.MOMENTUM_LABELS.get(report.momentum_rating, report.momentum_rating)
    trend_pl = t.TREND_LABELS.get(report.trend_label, report.trend_label)
    risk_pl = t.RISK_LABELS.get(report.risk_level, report.risk_level)

    score_table = Table([
        ["Ocena techniczna", "Jakość setupu", "Ryzyko", "Momentum", "Trend"],
        [f"{report.technical_score:.1f}/10", report.setup_quality,
         risk_pl, momentum_pl, trend_pl],
    ], colWidths=[3.4*cm]*5)
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2a44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), base_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [colors.HexColor("#eef2fa")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(score_table)
    flow.append(Spacer(1, 0.5 * cm))

    # Wykres jeśli przesłany
    if chart_png_bytes:
        try:
            img = Image(BytesIO(chart_png_bytes), width=17*cm, height=10*cm)
            flow.append(img)
            flow.append(Spacer(1, 0.4 * cm))
        except Exception:
            pass

    # Sekcje narracyjne
    sections = [
        ("Trend", report.trend_direction),
        ("Momentum", report.momentum_quality),
        ("Akumulacja instytucjonalna", report.institutional_read),
        ("Rozciągnięcie", report.extension_read),
        ("Wolumen", report.volume_confirmation),
        ("Zdrowie setupu", report.health_assessment),
    ]
    for title, text in sections:
        flow.append(Paragraph(title, h2))
        flow.append(Paragraph(text, body))

    flow.append(Spacer(1, 0.4 * cm))

    # Sygnały
    flow.append(Paragraph("Sygnały pozytywne", h2))
    if report.bullish_signals:
        items = [ListItem(Paragraph(s, body)) for s in report.bullish_signals]
        flow.append(ListFlowable(items, bulletType="bullet"))
    else:
        flow.append(Paragraph("— brak —", body))

    flow.append(Spacer(1, 0.2 * cm))
    flow.append(Paragraph("Sygnały ostrzegawcze", h2))
    if report.bearish_signals:
        items = [ListItem(Paragraph(s, body)) for s in report.bearish_signals]
        flow.append(ListFlowable(items, bulletType="bullet"))
    else:
        flow.append(Paragraph("— brak —", body))

    # Poziomy
    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Kluczowe poziomy", h2))
    sup = ", ".join(f"${s:.2f}" for s in report.supports) or "—"
    res = ", ".join(f"${r:.2f}" for r in report.resistances) or "—"
    flow.append(Paragraph(f"<b>Wsparcia:</b> {sup}", body))
    flow.append(Paragraph(f"<b>Opory:</b> {res}", body))
    flow.append(Paragraph(f"<b>Ostatnia cena:</b> ${report.last_close:.2f}", body))

    # Stopka
    flow.append(Spacer(1, 0.8 * cm))
    flow.append(Paragraph(
        "Wygenerowano przez Skaner Momentum. Dane: Yahoo Finance. "
        "Raport ma charakter edukacyjny i nie stanowi rekomendacji inwestycyjnej.",
        small,
    ))

    doc.build(flow)
    return buf.getvalue()
