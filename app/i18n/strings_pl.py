"""
strings_pl.py
==============

Centralny słownik polskich tłumaczeń.
Wszystkie etykiety UI i frazy analityczne w jednym miejscu — łatwo poprawić.
"""

# ---------------------------------------------------------------------------
# Etykiety główne / nawigacja
# ---------------------------------------------------------------------------
APP_TITLE = "Skaner Momentum"
APP_SUBTITLE = "AI-wspomagana analiza techniczna akcji"

NAV_ANALYSIS = "📊 Analiza pojedynczej spółki"
NAV_SCANNER = "🔭 Skaner rynku"
NAV_COMPARE = "⚖️ Porównywarka spółek"
NAV_WATCHLIST = "⭐ Lista obserwowanych"

# Sidebar
SIDEBAR_SETTINGS = "⚙️ Ustawienia"
SIDEBAR_TICKER = "Symbol giełdowy"
SIDEBAR_TICKER_HELP = "Wpisz dowolny ticker, np. NVDA, PLTR, HIMS, SOUN"
SIDEBAR_PERIOD = "Zakres historyczny"
SIDEBAR_QUICK = "**Szybki wybór:**"
SIDEBAR_ABOUT = "ℹ️ O aplikacji"
SIDEBAR_ABOUT_TEXT = (
    "**Skaner Momentum** to narzędzie do analizy technicznej w stylu "
    "inwestowania momentum. Wykorzystuje deterministyczny silnik regułowy "
    "(opcjonalnie wzbogacony o Claude API) oparty na heurystykach "
    "Minerviniego, O'Neila, Wyckoffa i nowoczesnych traderów momentum."
    "\n\n_Narzędzie edukacyjne — nie stanowi rekomendacji inwestycyjnej._"
)

# Period dropdown
PERIOD_LABELS = {
    "6mo": "6 miesięcy",
    "1y":  "1 rok",
    "2y":  "2 lata",
    "5y":  "5 lat",
}

# Stany
LOADING = "Ładowanie {symbol}…"
ERROR_FETCH = (
    "Nie udało się pobrać danych dla **{symbol}**. "
    "Sprawdź symbol i połączenie z internetem."
)
INFO_ENTER_TICKER = "👈 Wpisz symbol w panelu bocznym, aby rozpocząć."

# Nagłówki metryk w paskach
METRIC_SECTOR = "Sektor"
METRIC_INDUSTRY = "Branża"
METRIC_MARKET_CAP = "Kapitalizacja"
METRIC_AVG_VOLUME = "Średni wolumen"

LABEL_TECH_SCORE = "OCENA TECHNICZNA"
LABEL_OUT_OF = "z 10"
LABEL_SETUP = "JAKOŚĆ SETUPU"
LABEL_RISK = "POZIOM RYZYKA"
LABEL_MOMENTUM = "MOMENTUM"
LABEL_TREND = "TREND"

# Tytuły zakładek narracji
TAB_TREND = "📊 Trend"
TAB_MOMENTUM = "⚡ Momentum"
TAB_INSTITUTIONAL = "🏛️ Instytucje"
TAB_EXTENSION = "📏 Rozciągnięcie"
TAB_VOLUME = "📦 Wolumen"
TAB_HEALTH = "🩺 Zdrowie setupu"

# Sekcje główne
HEADER_COMMENTARY = "## 🧠 Komentarz analityka"
HEADER_FINAL = "## 📋 Podsumowanie końcowe"
HEADER_LEVELS = "📍 Kluczowe poziomy wsparcia / oporu"
HEADER_BULLISH = "### ✅ Sygnały byczy (pozytywne)"
HEADER_BEARISH = "### ⚠️ Sygnały niedźwiedzie (ostrzegawcze)"
NO_BULL_SIGNALS = "Brak wykrytych sygnałów pozytywnych."
NO_BEAR_SIGNALS = "Brak wykrytych sygnałów ostrzegawczych."

LEVEL_SUPPORTS = "**🟢 Strefy wsparcia (najbliższe pierwsze)**"
LEVEL_RESISTANCES = "**🔴 Strefy oporu (najbliższe pierwsze)**"
LEVEL_FROM_PRICE = "od ceny"
LEVEL_NONE = "_Brak wykrytych poziomów w zasięgu._"

FOOTER_DISCLAIMER = (
    "Dane: Yahoo Finance przez yfinance. Wskaźniki obliczane lokalnie. "
    "Analiza ma charakter edukacyjny — nie stanowi rekomendacji inwestycyjnej."
)

# ---------------------------------------------------------------------------
# Wartości słownikowe (etykiety klasyfikacji)
# ---------------------------------------------------------------------------
TREND_LABELS = {
    "Strong Uptrend":     "Silny trend wzrostowy",
    "Moderate Uptrend":   "Umiarkowany trend wzrostowy",
    "Sideways / Choppy":  "Konsolidacja / chaotyczny",
    "Moderate Downtrend": "Umiarkowany trend spadkowy",
    "Strong Downtrend":   "Silny trend spadkowy",
    "Insufficient data":  "Za mało danych",
}
MOMENTUM_LABELS = {
    "Powerful":  "Bardzo silne",
    "Strong":    "Silne",
    "Building":  "Budujące się",
    "Weak":      "Słabe",
    "Absent":    "Brak",
    "Insufficient data": "Za mało danych",
}
RISK_LABELS = {
    "Low":     "Niskie",
    "Medium":  "Średnie",
    "High":    "Wysokie",
    "Extreme": "Ekstremalne",
}

# Litera setupu (A+/A/B/C/D) zostawiamy uniwersalną — to standard.

# ---------------------------------------------------------------------------
# Sygnały — tłumaczenia "byczych" punktów
# ---------------------------------------------------------------------------
BULL_EMA_STACK = "Bycza struktura EMA (20 > 50 > 200) zachowana"
BULL_RSI_ZONE = "RSI w byczej strefie momentum z rosnącą strukturą"
BULL_MACD_POS = "MACD nad linią sygnału i powyżej zera"
BULL_HEALTHY_DISTANCE = "Zdrowy dystans nad EMA50, brak przewartościowania"
BULL_VOL_EXPAND = "Wolumen rośnie podczas wzrostów"
BULL_VOL_SPIKE = "Skok wolumenu (RVOL {rvol:.1f}×)"
BULL_BREAKOUT = "Wybicie powyżej ${level:.2f} potwierdzone"
BULL_ACCUMULATION = "Stosunek wolumenu wzrosty/spadki sprzyja akumulacji"
BULL_POCKET_PIVOT = "Wykryto pocket pivot (sygnał zainteresowania instytucji)"

# Sygnały niedźwiedzie
BEAR_EMA_STACK = "Niedźwiedzia struktura EMA (20 < 50 < 200)"
BEAR_RSI_OVERBOUGHT = "RSI w strefie wykupienia ({rsi:.0f})"
BEAR_RSI_OVERSOLD = "RSI w strefie wyprzedania ({rsi:.0f}) — momentum złamane"
BEAR_MACD_NEG = "MACD pod linią sygnału"
BEAR_EXTENDED = "Akcja klimaktycznie rozciągnięta nad EMA50"
BEAR_LIGHT_VOL = "Słaby wolumen na wzrostach — kiepskie potwierdzenie"
BEAR_DISTRIBUTION = "Wzorzec dystrybucji w wolumenie"
BEAR_BREAKDOWN = "Wybicie w dół poniżej ${level:.2f}"

# ---------------------------------------------------------------------------
# Narracja — frazy wstawiane do tekstu komentarza
# ---------------------------------------------------------------------------
TREND_BULLISH_STACK = (
    "Cena znajduje się powyżej EMA20, EMA50 i EMA200, a średnie ułożone są "
    "w prawidłowej byczej kolejności — to podręcznikowa struktura zdrowego "
    "trendu wzrostowego."
)
TREND_BEARISH_STACK = (
    "Wszystkie trzy EMA są ułożone niedźwiedzio, a cena znajduje się pod nimi — "
    "strukturalnie to trend spadkowy i wszelkie odbicia należy traktować "
    "podejrzliwie."
)
TREND_LT_UP_ST_DOWN = (
    "Trend długoterminowy jest wzrostowy (cena > EMA200), ale momentum "
    "krótkoterminowe się załamało — może to być zdrowa korekta lub początek "
    "dystrybucji."
)
TREND_MIXED = (
    "Struktura średnich kroczących jest mieszana — w tej chwili nie ma "
    "wyraźnego, wysokiej jakości trendu. Handel takim wykresem zwykle "
    "wypada gorzej niż czekanie na czysty setup."
)

RSI_OVERBOUGHT = (
    "RSI na poziomie {rsi:.1f} jest w strefie wykupienia — silne momentum, "
    "ale stosunek zysk/ryzyko nowych wejść tutaj jest niekorzystny."
)
RSI_BULL_ZONE = (
    "RSI na poziomie {rsi:.1f} jest w byczej 'strefie momentum' (55-70), "
    "a 9-okresowa MA RSI jest powyżej 21 — taka struktura charakteryzuje "
    "spółki będące liderami w prawdziwych trendach wzrostowych."
)
RSI_NEUTRAL = "RSI na poziomie {rsi:.1f} jest neutralny — momentum nie wybrało jeszcze strony."
RSI_OVERSOLD = (
    "RSI na poziomie {rsi:.1f} jest w strefie wyprzedania. Może poprzedzać "
    "odbicie, ale kupowanie wyprzedanych warunków w trendzie spadkowym to "
    "transakcja o niskim prawdopodobieństwie."
)
RSI_BELOW_50 = "RSI na poziomie {rsi:.1f} jest poniżej linii 50 — bias jest po stronie spadków."

MACD_BULL_ABOVE_ZERO = "MACD jest dodatni i powyżej swojego sygnału — potwierdza ruch w górę."
MACD_BULL_BELOW_ZERO = (
    "MACD przeciął linię sygnału w górę, ale wciąż jest ujemny — wczesny dowód "
    "zwrotu, który wymaga dalszego potwierdzenia."
)
MACD_BEAR = "MACD jest pod swoim sygnałem — momentum krótkoterminowe się zatrzymało lub odwróciło."

INST_ACCUMULATION = (
    "Wolumen w dni wzrostowe znacząco przewyższa wolumen w dni spadkowe "
    "w ciągu ostatniego miesiąca, a cena utrzymuje się powyżej EMA50 — "
    "ślad zgodny z akumulacją instytucjonalną."
)
INST_DISTRIBUTION = (
    "Wolumen w dni spadkowe przewyższa wolumen w dni wzrostowe w ciągu "
    "ostatniego miesiąca — to sygnatura dystrybucji, nie akumulacji."
)
INST_BALANCED = (
    "Wolumen w dni wzrostowe i spadkowe jest mniej więcej zrównoważony — "
    "brak wyraźnych dowodów akumulacji ani dystrybucji ze strony dużych graczy."
)
INST_POCKET_PIVOT = (
    " Najnowszy słupek wzrostowy uformował 'pocket pivot' (wolumen przekroczył "
    "największy wolumen dnia spadkowego z ostatnich 10 sesji) — to wczesny "
    "sygnał zainteresowania instytucji w stylu Gila Moralesa / O'Neila."
)

EXT_CLIMACTIC = (
    "Cena jest {atr:.1f} ATR powyżej EMA50 — akcja jest rozciągnięta. "
    "Takie ekstrema 3. fazy często rozwiązują się gwałtownymi korektami; "
    "kupowanie w tym miejscu to słaba statystyka."
)
EXT_MODERATE = (
    "Cena jest {atr:.1f} ATR powyżej EMA50 — umiarkowanie rozciągnięta. "
    "Lepsze wejścia zwykle pojawiają się przy korekcie do 20-dniowej "
    "lub po wąskiej konsolidacji."
)
EXT_SWEET_SPOT = (
    "Cena utrzymuje się komfortowo powyżej EMA50 bez nadmiernego rozciągnięcia — "
    "to 'słodki punkt' dla wejść momentum przy sile."
)
EXT_BELOW_EMA50 = (
    "Cena jest poniżej EMA50 — z definicji nie jest rozciągnięta, ale też "
    "nie jest w trybie trendu. Czekaj na odzyskanie EMA50, zanim potraktujesz "
    "tę spółkę jako kandydata momentum."
)
EXT_NEAR_EMA50 = "Cena waha się w okolicy EMA50 ({pct:+.1f}% vs EMA20)."

VOL_SPIKE = (
    "Dzisiejszy względny wolumen wynosi {rvol:.2f}× średniej 20-dniowej — "
    "wyraźny skok wolumenu. Jeśli akcja jest wzrostowa, to potwierdzenie, "
    "którego oczekują traderzy momentum."
)
VOL_EXPANDING = (
    "Średnia RVOL z ostatniego tygodnia wynosi {rvol:.2f}× — wolumen rośnie "
    "wraz z ceną, czyli to czego oczekuje się przy akumulacji."
)
VOL_LIGHT = (
    "RVOL na poziomie {rvol:.2f}× — cena rośnie, ale wolumen jest słaby. "
    "Ruchy na malejącym wolumenie często zawodzą; traktuj ten wzrost ostrożnie."
)
VOL_NORMAL = (
    "Wolumen jest mniej więcej normalny (5-dniowa RVOL {rvol:.2f}×) — "
    "ani potwierdzenie, ani ostrzeżenie."
)

BREAKOUT_NOTE_UP = (
    " Wybicie powyżej 50-dniowego maksimum (~${level:.2f}) zostało potwierdzone "
    "w ostatnich 2 sesjach."
)
BREAKOUT_NOTE_DOWN = (
    " Cena przebiła W DÓŁ 50-dniowe minimum (~${level:.2f}) — strukturalny minus."
)

HEALTH_GOOD = (
    "Setup wygląda zdrowo. Trend, momentum i struktura są zgodne, a akcja "
    "nie jest jeszcze klimaktycznie rozciągnięta."
)
HEALTH_EXTENDED = (
    "Trend jest nienaruszony, ale akcja jest rozciągnięta — stosunek zysk/ryzyko "
    "nowych wejść jest tu słaby. Obecni posiadacze mogą zarządzać przez "
    "podążające stop-lossy."
)
HEALTH_DANGEROUS = (
    "Setup wygląda niebezpiecznie. Ocena trendu jest słaba, a momentum poniżej "
    "linii 50 — kupowanie słabości tutaj bez wyraźnego sygnału odwrócenia "
    "to transakcja o niskim prawdopodobieństwie."
)
HEALTH_MIXED = (
    "Setup jest mieszany — niektóre elementy są na miejscu, inne nie. "
    "Cierpliwość, aż pojawi się czyste wybicie lub głębszy reset, zwykle "
    "bije forsowanie transakcji."
)
