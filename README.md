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

### 5. Moduł Skuteczności i Ewaluacji AI (12:30)
- Codziennie o **12:30** (oraz komendą `!accuracy` / `!skutecznosc`) bot weryfikuje trafność zaleceń z porannego briefu w oparciu o rzeczywiste zmiany cenowe:
  - **0 – 25%**: ❌ **Analiza nieudana**
  - **25 – 75%**: ⚖️ **Analiza neutralna**
  - **75 – 100%**: 🎯 **Analiza udana**
- Raport zawiera: **Globalny counter** (łączny win-rate, rozkład udanych/neutralnych/nieudanych), **wynik ostatniego briefu** oraz **wnioski i lekcje rynkowe AI**.

---

## 💬 Komendy Bota & Uprawnienia

> 🔒 **Autoryzacja**: Dostęp do wywoływania wszystkich komend Newsbox mają wyłącznie **Administratorzy** oraz użytkownicy z rolą **`Newsbox-vip`**.

| Komenda | Wymagana Rola | Opis |
| :--- | :--- | :--- |
| `!briefing` / `!poranek` | Admin / Newsbox-vip | Pełny poranny raport makro (FX Majors, DXY, DAX, plan sesji). |
| `!briefing <walor>` | Admin / Newsbox-vip | Dedykowana analiza dla 1 wybranego waloru (np. `!briefing DAX`, `!briefing BTC`). |
| `!accuracy` / `!skutecznosc` | Admin / Newsbox-vip | Raport skuteczności: globalny counter, punktacja briefu i wnioski AI. |
| `!portfolio` / `!portfel` | Admin / Newsbox-vip | Wyświetla podgląd Twoich spółek, notowania i podsumowanie AI. |
| `!portfolio add <symbol>` | Admin / Newsbox-vip | Dodaje spółkę do portfela (np. `!portfolio add CDR.WA`, `!portfolio add NVDA`). |
| `!portfolio remove <symbol>`| Admin / Newsbox-vip | Usuwa spółkę z portfela (np. `!portfolio remove TSLA`). |
| `!portfolio news` | Admin / Newsbox-vip | Wiadomości i komunikaty dopasowane tylko do rynków spółek z portfela. |
| `!calendar` / `!kalendarz` | Admin / Newsbox-vip | Kalendarz ekonomiczny dnia z oceną ryzyk AI. |
| `!market` / `!notowania` | Admin / Newsbox-vip | Szybki podgląd cen śledzonych instrumentów bazowych. |
| `!news pl` | Admin / Newsbox-vip | Newsy z Polski i parkietu GPW (Parkiet, Bankier). |
| `!news us` / `!news usa` | Admin / Newsbox-vip | Wiadomości z USA i Wall Street (CNBC, MarketWatch). |
| `!news crypto` / `!crypto` | Admin / Newsbox-vip | Najświeższe wiadomości ze świata kryptowalut i Web3. |
| `!news global` | Admin / Newsbox-vip | Rynki globalne, surowce i makro (Reuters, Euronews). |
| `!set_channel <typ>` | Admin | Przypisuje kanał (`macro`, `calendar`, `news_pl`, `news_global`, `crypto`, `portfolio`, `portfolio_news`). |
| `!channels` | Admin / Newsbox-vip | Wyświetla mapowanie kanałów powiadomień. |
| `!reload_prompts` | Admin | Przeładowuje szablony promptów z folderu `prompts/` w locie. |
| `!status` | Admin / Newsbox-vip | Wyświetla stan techniczny i konfigurację bota. |
| `!ping` | Admin / Newsbox-vip | Sprawdza opóźnienie bota. |

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
