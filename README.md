# 🗞️ Newsbox — AI Macro & Trading Advisor Discord Bot

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Powered by Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

**Newsbox** to zaawansowany bot Discord wspierający traderów i inwestorów codziennym briefingiem makro o **8:00 rano**, doradztwem transakcyjnym AI (**co handlować 🟢 / czego unikać ⛔**), kalendarzem ekonomicznym oraz potokiem wiadomości biznesowych z **Polski (Parkiet/GPW), Europy, USA i świata**.

---

## 🌟 Główne Funkcjonalności

1. **🌅 Poranny Briefing Makro & Trader Advisory (8:00 AM)**:
   - Podsumowanie otwarcia sesji i reżimu rynkowego (*Risk-On / Risk-Off / Neutral*).
   - **🟢 Co można dzisiaj handlować (In Play)**: Aktywa z jasnym układem technicznym i wsparciem makro.
   - **⛔ Czego dzisiaj nie handlować (No-Trade)**: Instrumenty o podwyższonym ryzyku lub zagrażające nagłą zmiennością przed odczytami makro.
   - **📋 Plan sesji**: Kluczowe godziny, poziomy katalizatorów i zarządzanie ryzykiem.

2. **📰 Multi-Region News Feed (PL, EU, USA, Świat)**:
   - **Polska**: Parkiet.com, Bankier.pl (Gospodarka i Wiadomości GPW).
   - **USA & Europa**: CNBC, Reuters, MarketWatch, Euronews.
   - **Krypto & Surowce**: CoinDesk, notowania ropy i złota.

3. **📈 W Pełni Konfigurowalne Aktywa**:
   - Domyślnie śledzi: **DXY**, **EUR/USD**, **DAX**, **BTC**.
   - Łatwo rozszerzalny o **WIG20**, **S&P 500**, **Złoto (GOLD)**, **Ropę (OIL)** w konfiguracji `TICKERS`.

4. **📅 Kalendarz Ekonomiczny & Ostrzeżenia AI**:
   - Wykaz publikacji z podziałem na wagi (🔴 Wysoki / 🟡 Średni).
   - Wskazówki AI o krytycznych oknach czasowych (np. publikacja CPI o 14:30).

5. **📡 Multi-Channel Routing na Discordzie**:
   - Kierowanie poszczególnych raportów do dedykowanych kanałów (np. `#raport-makro`, `#kalendarz`, `#news-polska`, `#news-swiat`).

6. **🧠 Edytowalne Szablony Promptów Gemini (`prompts/`)**:
   - Wszystkie prompty analizy AI znajdują się w edytowalnych plikach `.txt` w katalogu `prompts/`.
   - Możliwość modyfikacji stylu i strategii w dowolnym momencie oraz przeładowania na żywo komendą `!reload_prompts`.

---

## 🏗️ Architektura Projektu

```
Newsbox---discord-bot/
├── prompts/                         # 📝 Edytowalne szablony promptów Gemini AI
│   ├── trader_advisory.txt          # Prompt doradztwa tradingowego (Do's & Don'ts)
│   ├── calendar_analysis.txt        # Prompt oceny ryzyka kalendarza
│   └── news_summary.txt             # Prompt syntezy wiadomości regionalnych
├── .github/
│   ├── ISSUE_TEMPLATE/              # Szablony zgłoszeń GitHub (User Story, Bug, Tech Story)
│   │   ├── user_story.yml
│   │   ├── bug_report.yml
│   │   ├── tech_story.yml
│   │   └── config.yml
│   ├── labels.yml                   # Definicje etykiet GitHub
│   └── LABELS.md                    # Przewodnik po etykietach i workflow
├── src/
│   └── newsbox/
│       ├── __init__.py
│       ├── __main__.py              # Główny punkt startowy (`python -m newsbox`)
│       ├── bot.py                   # Cykl życia bota i poranny dispatcher
│       ├── config.py                # Obsługa zmiennych środowiskowych i routingu kanałów
│       ├── cogs/                    # Komendy i moduły Discord
│       │   ├── briefings.py         # !briefing, !calendar, !market
│       │   ├── news.py              # !news [pl|usa|eu|global|all]
│       │   ├── channels.py          # !set_channel, !channels (routing)
│       │   └── admin.py             # !status, !ping, !reload_prompts
│       ├── services/                # Logika integracji i pobierania danych
│       │   ├── gemini_service.py    # Integracja Google Gemini API + prompt loader
│       │   ├── market_service.py    # Pobieranie notowań giełdowych (yfinance)
│       │   ├── calendar_service.py  # Kalendarz makroekonomiczny
│       │   ├── news_service.py      # Agregator wiadomości (Parkiet, Bankier, CNBC)
│       │   └── scheduler_service.py # Harmonogram 8:00 AM (APScheduler)
│       └── utils/
│           ├── embeds.py            # Generatory embedów Discord
│           └── logger.py            # Konfiguracja logowania
├── tests/                           # Zestaw testów jednostkowych (pytest)
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_embeds.py
│   └── test_services.py
├── .env.example                     # Wzorzec konfiguracji
├── .geminiignore                    # Optymalizacja tokenów dla Antigravity / Gemini
├── .gitignore                       # Ignorowane pliki gita
├── Dockerfile                       # Obraz Dockera
├── docker-compose.yml               # Uruchamianie w kontenerze
└── pyproject.toml                   # Konfiguracja projektu Python
```

---

## 🚀 Szybki Start

### 1. Wymagania
- **Python 3.10+**
- **Token bota Discord** ([Discord Developer Portal](https://discord.com/developers/applications))
- **Klucz Google Gemini API** ([Google AI Studio](https://aistudio.google.com/))

### 2. Instalacja i konfiguracja
```bash
# 1. Klonowanie repozytorium
git clone https://github.com/koniu-rav/Newsbox---discord-bot.git
cd Newsbox---discord-bot

# 2. Środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalacja zależności
pip install -r requirements-dev.txt

# 4. Konfiguracja pliku .env
cp .env.example .env
```

Uzupełnij w pliku `.env` swoje klucze `DISCORD_BOT_TOKEN` i `GEMINI_API_KEY`.

### 3. Uruchomienie bota

**Lokalnie:**
```bash
python -m newsbox
```

**Przez Docker Compose:**
```bash
docker-compose up -d --build
```

---

## 💬 Komendy Bota

| Komenda | Uprawnienia | Opis |
| :--- | :--- | :--- |
| `!briefing` / `!poranek` | Wszyscy | Generuje natychmiastowy raport makro i doradztwo AI na bieżącym kanale. |
| `!calendar` / `!kalendarz` | Wszyscy | Wyświetla dzisiejsze publikacje makro i wskazówki AI dla tradera. |
| `!market` / `!notowania` | Wszyscy | Wyświetla szybki podgląd notowań śledzonych instrumentów (DXY, EUR/USD, DAX, BTC...). |
| `!news pl` | Wszyscy | Najnowsze wiadomości z polskiego rynku i parkietu GPW (Parkiet, Bankier). |
| `!news us` / `!news usa` | Wszyscy | Wiadomości z rynków USA i Wall Street (CNBC, MarketWatch). |
| `!news global` | Wszyscy | Wiadomości ze świata, krypto i surowce (Reuters, CoinDesk). |
| `!news all` | Wszyscy | Pełny przegląd newsów ze wszystkich rynków. |
| `!set_channel <typ>` | Admin | Ustawia kanał dla powiadomień (`macro`, `calendar`, `news_pl`, `news_global`). |
| `!channels` | Wszyscy | Pokazuje aktualne przypisanie kanałów Discord. |
| `!reload_prompts` | Admin | Przeładowuje szablony promptów z folderu `prompts/` bez restartu bota. |
| `!status` | Wszyscy | Wyświetla status bota, model AI i listę śledzonych aktywów. |
| `!ping` | Wszyscy | Sprawdza opóźnienie (ping) bota. |

---

## 🧪 Testy

```bash
# Uruchomienie testów jednostkowych
pytest

# Testy z raportem pokrycia kodu
pytest --cov=newsbox tests/
```

---

## 📄 Licencja
Projekt na licencji Apache 2.0. Zobacz plik [LICENSE](LICENSE) po szczegóły.
