# 📈 Skaner Momentum (v2 — pełna wersja PL)

Lokalna aplikacja webowa do analizy technicznej akcji w stylu inwestowania momentum. Cały interfejs i analiza po polsku.

---

## ✨ Co nowego w v2

- 🇵🇱 **Pełna polonizacja** — UI, narracje, sygnały, wszystko po polsku
- 🔭 **Skaner rynku** — przeskanuj 20-50 spółek równolegle, zobacz ranking
- ⚖️ **Porównywarka** — 2-3 spółki obok siebie, znormalizowane wykresy zwrotów
- 🤖 **Claude API** — opcjonalna pogłębiona analiza AI (3-4 akapity narracji)
- 🔔 **Alerty** — e-mail (SMTP) + Telegram dla najlepszych setupów
- 📐 **Dodatkowe wskaźniki** — Bollinger Bands, ADX/+DI/-DI, OBV, VWAP
- 📄 **Eksport PDF** — kompletny raport do pobrania jednym kliknięciem

Wszystko z v1 działa jak wcześniej (świece, EMA20/50/200, RSI z MA, MACD, RVOL, S/R, breakout detection, ocena 1-10, momentum rating, setup quality, risk level).

---

## 📁 Struktura projektu

```
momentum_scanner/
├── streamlit_app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml
└── app/
    ├── i18n/                    # 🆕 polskie tłumaczenia
    │   └── strings_pl.py
    ├── core/                    # silnik analizy
    │   ├── data_fetcher.py
    │   ├── indicators.py        # EMA/RSI/MACD/RVOL/ATR/breakout
    │   ├── indicators_extra.py  # 🆕 Bollinger/ADX/OBV/VWAP
    │   ├── ai_analyst.py        # silnik regułowy (PL)
    │   └── chart_builder.py     # 🆕 + porównywarka
    ├── services/                # 🆕 cały folder
    │   ├── llm_analyst.py       # Claude API
    │   ├── scanner.py           # batch scan (wątki)
    │   ├── alerts.py            # SMTP + Telegram
    │   └── pdf_export.py        # ReportLab
    ├── ui/main_view.py          # multi-page (Analiza/Skaner/Porównywarka)
    └── utils/formatters.py      # PL etykiety + kolory
```

---

## 🛠 Instalacja

Jeśli masz już v1 zainstalowaną — wystarczy podmienić pliki i doinstalować nowe biblioteki:

```bash
cd ~/Downloads/momentum_scanner
source .venv/bin/activate
pip install -r requirements.txt    # doinstaluje reportlab, requests
streamlit run streamlit_app.py
```

Jeśli zaczynasz od zera:

```bash
cd ~/Downloads
unzip momentum_scanner_v2.zip
cd momentum_scanner
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

App otworzy się na **http://localhost:8501**.

---

## 🎯 Użycie

### Strona 1 — Analiza pojedynczej spółki
Wpisujesz ticker → dostajesz wszystko co w v1, plus:
- przełączniki **Bollinger Bands** i **VWAP** nad wykresem
- panel ADX / +DI/-DI / BB Width / OBV trend pod wykresem
- przycisk **🤖 Pogłębiona analiza Claude** (jeśli klucz ustawiony)
- przycisk **📄 Generuj raport PDF** → pobranie pliku

### Strona 2 — Skaner rynku
Wybierasz uniwersum (predefiniowane: AI/Półprzewodniki, Mega-cap tech, Momentum, Fintech, Biotech, Cloud — albo własna lista) → klikasz **Skanuj** → tabela z oceną dla każdej spółki, sortowalna i filtrowalna. Pasek postępu pokazuje stan pracy.

W rozwijanej sekcji **🔔 Wyślij alerty** możesz ustawić kryteria (min. ocena, min. sygnały bycze, max. ryzyko) i wysłać e-mail lub Telegram dla spółek przechodzących filtr.

### Strona 3 — Porównywarka
Wpisujesz 2-3 tickery → wykres znormalizowanych zwrotów (od pierwszego dnia okresu, w %) + tabela porównawcza ze wszystkimi metrykami obok siebie + krótkie tezy.

---

## 🔌 Konfiguracja integracji

### Claude API (opcjonalne — pogłębiona analiza)

1. Doinstaluj pakiet:
   ```bash
   pip install anthropic
   ```

2. Pobierz klucz z **console.anthropic.com**.

3. Ustaw w jeden z trzech sposobów (kolejność precedencji od góry):

   **A. Zmienna środowiskowa** (najprościej):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   streamlit run streamlit_app.py
   ```

   **B. `.streamlit/secrets.toml`** (per-projekt, gitignored):
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

   **C. Dopisanie do `~/.zshrc`** (na stałe, dla wszystkich sesji):
   ```bash
   echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
   source ~/.zshrc
   ```

Domyślny model to `claude-opus-4-7`. Aby zmienić — `export ANTHROPIC_MODEL="claude-sonnet-4-6"` (Sonnet jest tańszy i szybszy).

### Alerty e-mail (SMTP)

Dla Gmaila — wygeneruj **hasło aplikacji** w ustawieniach Google (Konto Google → Bezpieczeństwo → Hasła aplikacji). Nie używasz głównego hasła.

Dodaj do `.streamlit/secrets.toml`:
```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "twoj@gmail.com"
SMTP_PASS = "xxxx xxxx xxxx xxxx"   # hasło aplikacji, 16 znaków
ALERT_EMAIL_TO = "twoj@gmail.com"   # gdzie wysyłać alerty
```

### Alerty Telegram

1. W Telegramie napisz do **@BotFather** → `/newbot` → ustal nazwę → dostaniesz token.
2. Napisz do swojego bota dowolną wiadomość (musi się poznać z Tobą).
3. Otwórz `https://api.telegram.org/bot<TWÓJ_TOKEN>/getUpdates` → znajdź `"chat":{"id": 123456789, ...}`.
4. Dodaj do `.streamlit/secrets.toml`:
   ```toml
   TELEGRAM_BOT_TOKEN = "1234567890:ABC..."
   TELEGRAM_CHAT_ID = "123456789"
   ```

---

## 🔮 Co dalej?

Architektura zostawia czyste seamy na kolejne funkcje. Najłatwiej dodać:

- **Zapis watchlisty na dysk** — JSON w `~/.momentum_scanner/`, ładowany przy starcie. (Jak będziesz chciał, zrobię w następnej iteracji.)
- **Cron / scheduled scan** — `app/services/cron_runner.py` z `APScheduler` puszczany w tle, robi nightly scan i pcha alerty automatycznie.
- **TradingView embed** — `st.components.v1.html` z oficjalnym widget snippet.
- **Ranking AI** — top 50 ze skanu → batch prompt do Claude → wybór 10 z najlepszą jakością narracji.
- **Backtesting setupu** — vectorbt lub backtrader na historycznych score'ach.

---

## ⚠️ Zastrzeżenia

Aplikacja służy wyłącznie do celów **edukacyjnych i badawczych**. Nie stanowi rekomendacji inwestycyjnej. Zawsze rób własną analizę i konsultuj się z licencjonowanym doradcą przy decyzjach o realnym kapitale.

## 📜 Licencja

MIT.
