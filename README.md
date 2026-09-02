# 🗞️ Newsbox — AI Macro, Crypto & Portfolio Bot by we.trade

[![we.trade Community](https://img.shields.io/badge/Community-we.trade-1ABC9C.svg)](https://discord.gg)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Powered by Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

**Newsbox** to zaawansowany bot Discord stworzony z myślą o społeczności **we.trade**, wspierający traderów i inwestorów w podejmowaniu decyzji:
1. **🌅 Porannym briefingiem makro o 8:00 (Pon–Pt)** z naciskiem na **FX Majors (EUR/USD, GBP/USD, USD/JPY), DXY oraz DAX** i oceną **co handlować 🟢 / czego unikać ⛔**.
2. **🎯 Briefingiem na żądanie dla 1 wybranego waloru** (np. `!briefing DAX`, `!briefing BTC`, `!briefing TSLA`).
3. **💼 Śledzeniem spółek z Twojego portfela** (`!portfolio`, `!portfolio add`, `!portfolio news`) z agregacją komunikatów z Wall Street, Krypto i GPW.
4. **🪙 Dedykowanym kanałem krypto (`#crypto-chat`)** z wiadomościami z CoinDesk, Cointelegraph i Decrypt.
5. **⏳ Cichymi oknami czasowymi (Market Open Quiet Windows)** – brak zbędnych powiadomień podczas startu sesji europejskiej (08:50-09:15) i amerykańskiej (15:20-15:45).
6. **📅 Kalendarzem ekonomicznym o 7:00 (Pon–Pt)** z zaleceniami AI dotyczącymi okien zmienności.
7. **📊 Modułem Skuteczności o 12:30 (Pon–Pt)** — weryfikacja trafności zaleceń, globalny licznik i wnioski rynkowe.

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
- Przeglądaj bieżące notowania i wygenerowane podsumowanie newsów tylko dla rynków Twoich spółek (`!portfolio news`).

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

> 🔒 **Autoryzacja**: Dostęp do wywoływania komend bota mają wyłącznie **Administratorzy** oraz użytkownicy z rolą **`Newsbox-vip`** w społeczności **we.trade**.

| Komenda | Wymagana Rola | Opis |
| :--- | :--- | :--- |
| `!briefing` / `!poranek` | Admin / Newsbox-vip | Briefing dla aktualnie nadchodzącej sesji handlowej (Londyn, NY lub Azja). |
| `!weekly` / `!tydzien` | Admin / Newsbox-vip | 🗓️ Strategiczny plan i horyzont makro na cały nadchodzący tydzień (Niedziela 10:00). |
| `!london` / `!londyn` | Admin / Newsbox-vip | 🇬🇧 Briefing Sesji Londyńskiej (07:00 CET — 1h przed pre-marketem Europy/DAX). |
| `!ny` / `!nowyjork` | Admin / Newsbox-vip | 🇺🇸 Briefing Sesji Nowojorskiej (13:30 CET — 1h przed danymi USA i Wall St). |
| `!asia` / `!azja` | Admin / Newsbox-vip | 🇯🇵 Briefing Sesji Azjatyckiej (23:00 CET — 1h przed sesją Tokio/Sydney). |
| `!briefing <walor>` | Admin / Newsbox-vip | Dedykowana analiza dla 1 wybranego waloru (np. `!briefing DAX`, `!briefing BTC`). |
| `!accuracy` / `!skutecznosc` | Admin / Newsbox-vip | 📊 Wielopoziomowy raport skuteczności: Globalny, Tygodniowy i Rozbicie na Sesje. |
| `!portfolio` / `!portfel` | Admin / Newsbox-vip | Wyświetla podgląd Twoich spółek, notowania i podsumowanie AI. |
| `!portfolio add <symbol>` | Admin / Newsbox-vip | Dodaje spółkę do portfela (np. `!portfolio add CDR.WA`, `!portfolio add NVDA`). |
| `!portfolio remove <symbol>`| Admin / Newsbox-vip | Usuwa spółkę z portfela (np. `!portfolio remove TSLA`). |
| `!portfolio news` | Admin / Newsbox-vip | Wiadomości i komunikaty dopasowane tylko do rynków spółek z portfela. |
| `!calendar` / `!kalendarz` | Admin / Newsbox-vip | Kalendarz ekonomiczny dnia z oceną ryzyk AI. |
| `!market` / `!notowania` | Admin / Newsbox-vip | Szybki podgląd cen śledzonych instrumentów bazowych. |
| `!wetrade` / `!about` | Admin / Newsbox-vip | Informacje o społeczności we.trade i modułach bota. |
| `!news pl` | Admin / Newsbox-vip | Newsy z Polski i parkietu GPW (Parkiet, Bankier). |
| `!news us` / `!news usa` | Admin / Newsbox-vip | Wiadomości z USA i Wall Street (CNBC, MarketWatch). |
| `!news crypto` / `!crypto` | Admin / Newsbox-vip | Najświeższe wiadomości ze świata kryptowalut i Web3. |
| `!news global` | Admin / Newsbox-vip | Rynki globalne, surowce i makro (Reuters, Euronews). |
| `!flash` / `!flashnews` | Admin / Newsbox-vip | Błyskawiczna migawka newsowa AI (co, kiedy, wpływ na walory — auto o :25 i :55). |
| `!set_channel <typ>` | Admin | Przypisuje kanał (`macro`, `calendar`, `news_pl`, `news_global`, `crypto`, `portfolio`, `portfolio_news`). |
| `!channels` | Admin / Newsbox-vip | Wyświetla mapowanie kanałów powiadomień. |
| `!reload_prompts` | Admin | Przeładowuje szablony promptów z folderu `prompts/` w locie. |
| `!status` | Admin / Newsbox-vip | Wyświetla stan techniczny, konfigurację bota i branding we.trade. |
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
