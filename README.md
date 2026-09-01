# 🗞️ Newsbox — AI Macro, Crypto & Portfolio Discord Bot

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Powered by Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

**Newsbox** to zaawansowany bot Discord wspierający traderów i inwestorów:
1. **🌅 Porannym briefingiem makro o 8:00** z naciskiem na **FX Majors (EUR/USD, GBP/USD, USD/JPY), DXY oraz DAX** i oceną **co handlować 🟢 / czego unikać ⛔**.
2. **🎯 Briefingiem na żądanie dla 1 wybranego waloru** (np. `!briefing DAX`, `!briefing BTC`, `!briefing TSLA`).
3. **💼 Śledzeniem spółek z Twojego portfela** (`!portfolio`, `!portfolio add`, `!portfolio news`) z agregacją komunikatów z GPW i Wall Street.
4. **🪙 Dedykowanym kanałem krypto (`#crypto-chat`)** z wiadomościami z CoinDesk, Cointelegraph i Decrypt.
5. **⏳ Cichymi oknami czasowymi (Market Open Quiet Windows)** – brak zbędnych powiadomień podczas startu sesji europejskiej (08:50-09:15) i amerykańskiej (15:20-15:45).
6. **📅 Kalendarzem ekonomicznym o 8:00** z zaleceniami AI dotyczącymi okien zmienności.

---

## 🌟 Główne Funkcjonalności

### 1. Raport Makro o 8:00 & Doradztwo AI
- **FX Majors & DXY**: Analiza siły dolara, perspektywy dla EUR/USD, GBP/USD, USD/JPY.
- **DAX & Europa**: Poziomy na otwarcie rynku kasowego o 09:00.
- **🟢 Co handlować / ⛔ Czego unikać**: Jasny podział instrumentów z planem sesji i zarządzaniem ryzykiem.

### 2. Briefing dla Pojedynczego Waloru
- Wpisz w dowolnym momencie np. `!briefing DAX`, `!briefing BTC` lub `!briefing CDR.WA`, aby otrzymać szybką analizę AI dedykowaną tylko dla tego jednego instrumentu.

### 3. Moduł Portfela Inwestycyjnego (`!portfolio`)
- Zarządzaj listą swoich spółek bezpośrednio z Discorda (`!portfolio add CDR.WA`, `!portfolio remove TSLA`).
- Przeglądaj bieżące notowania i wygenerowane podsumowanie newsów tylko dla Twoich spółek (`!portfolio news`).

### 4. Dedykowany Strumień Krypto (`#crypto-chat`)
- Agregacja z najważniejszych serwisów krypto: CoinDesk, Cointelegraph, Decrypt.
- Komendy: `!news crypto` lub `!crypto`.

### 5. Multi-Channel Routing na Discordzie
- Osobne kanały dla poszczególnych rodzajów raportów:
  - `macro`: Briefing poranny i FX/DAX Advisory o 8:00.
  - `calendar`: Kalendarz publikacji makroekonomicznych.
  - `news_pl`: Newsy z Polski, GPW i Parkietu.
  - `news_global`: Newsy z USA, Wall Street i rynków światowych.
  - `crypto`: Kanał krypto (`#crypto-chat`).
  - `portfolio`: Wiadomości dla spółek z Twojego portfela.

---

## 💬 Komendy Bota

| Komenda | Uprawnienia | Opis |
| :--- | :--- | :--- |
| `!briefing` / `!poranek` | Wszyscy | Pełny poranny raport makro (FX Majors, DXY, DAX, plan sesji). |
| `!briefing <walor>` | Wszyscy | Dedykowana analiza dla 1 wybranego waloru (np. `!briefing DAX`, `!briefing BTC`). |
| `!portfolio` / `!portfel` | Wszyscy | Wyświetla podgląd Twoich spółek, notowania i podsumowanie AI. |
| `!portfolio add <symbol>` | Wszyscy | Dodaje spółkę do portfela (np. `!portfolio add CDR.WA`, `!portfolio add NVDA`). |
| `!portfolio remove <symbol>`| Wszyscy | Usuwa spółkę z portfela (np. `!portfolio remove TSLA`). |
| `!portfolio news` | Wszyscy | Wiadomości i komunikaty ESPI/EBI tylko dla spółek z portfela. |
| `!calendar` / `!kalendarz` | Wszyscy | Kalendarz ekonomiczny dnia z oceną ryzyk AI. |
| `!market` / `!notowania` | Wszyscy | Szybki podgląd cen śledzonych instrumentów bazowych. |
| `!news pl` | Wszyscy | Newsy z Polski i parkietu GPW (Parkiet, Bankier). |
| `!news us` / `!news usa` | Wszyscy | Wiadomości z USA i Wall Street (CNBC, MarketWatch). |
| `!news crypto` / `!crypto` | Wszyscy | Najświeższe wiadomości ze świata kryptowalut i Web3. |
| `!news global` | Wszyscy | Rynki globalne, surowce i makro (Reuters, Euronews). |
| `!set_channel <typ>` | Admin | Przypisuje kanał (`macro`, `calendar`, `news_pl`, `news_global`, `crypto`, `portfolio`). |
| `!channels` | Wszyscy | Wyświetla mapowanie kanałów powiadomień. |
| `!reload_prompts` | Admin | Przeładowuje szablony promptów z folderu `prompts/` w locie. |
| `!status` | Wszyscy | Wyświetla stan techniczny i konfigurację bota. |
| `!ping` | Wszyscy | Sprawdza opóźnienie bota. |

---

## 🚀 Uruchomienie

### Środowisko lokalne
```bash
# Aktywacja środowiska
source .venv/bin/activate

# Uruchomienie bota
python -m newsbox
```

### Docker Compose
```bash
docker compose up -d --build
```

---

## 🧪 Testy

```bash
# Uruchomienie testów z pytest
pytest
```
