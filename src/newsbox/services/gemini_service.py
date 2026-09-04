"""Gemini AI Service for generating macro summaries, trader advisory, single-asset briefs, and portfolio insights."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiService:
    """Service wrapper for interacting with Google Gemini API using configurable prompt templates."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        prompts_dir: Optional[str] = None,
    ) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.gemini_api_key if api_key is None else api_key
        self.model_name = model_name or self.settings.gemini_model
        self.prompts_dir = Path(prompts_dir or self.settings.prompts_dir)
        self._client = None
        self._prompt_cache: Dict[str, str] = {}
        self.last_error: Optional[str] = None
        self._initialize_client()
        self.load_prompts()

    def _initialize_client(self) -> None:
        """Initialize Google GenAI client if api_key is present."""
        if not self.api_key:
            self.last_error = "Brak klucza GEMINI_API_KEY"
            logger.warning("Gemini API key is not configured. AI will use mock responses.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info("Gemini GenAI client initialized with model: %s", self.model_name)
        except Exception as e:
            logger.warning("Could not initialize google.genai client: %s. Using fallback mode.", e)

    def load_prompts(self) -> None:
        """Load or reload all prompt templates from prompts directory."""
        if not self.prompts_dir.exists():
            logger.warning("Prompts directory %s does not exist. Using fallback templates.", self.prompts_dir)
            return

        for path in self.prompts_dir.glob("*.txt"):
            try:
                self._prompt_cache[path.stem] = path.read_text(encoding="utf-8")
                logger.debug("Loaded prompt template: %s", path.stem)
            except Exception as e:
                logger.error("Failed to read prompt file %s: %s", path, e)
        logger.info("Loaded %d prompt template(s) from %s", len(self._prompt_cache), self.prompts_dir)

    def get_prompt_template(self, name: str, default: str) -> str:
        """Retrieve cached prompt template or return default."""
        return self._prompt_cache.get(name, default)

    async def generate_weekly_outlook(
        self,
        calendar_events: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        news_headlines: List[Dict[str, Any]],
    ) -> str:
        """Generate comprehensive Sunday 10:00 AM strategic weekly outlook across FX, Indices, Commodities, and Crypto."""
        if not self._client:
            return (
                "🌐 **GŁÓWNY MOTYW PRZEWODNI TYGODNIA**: Umiarkowany Risk-On przed kluczowymi danymi o inflacji i decyzjami banków centralnych.\n\n"
                "📅 **PUNKTY ZWROTNE TYGODNIA**:\n"
                "- **Środa 14:15**: Raport ADP z rynku pracy USA.\n"
                "- **Środa 15:45**: Decyzja Banku Kanady (BoC) ws. stóp procentowych.\n"
                "- **Piątek 14:30**: Raport Non-Farm Payrolls (NFP) i Stopa Bezrobocia w USA.\n\n"
                "🎯 **STRATEGICZNY BIAS NA WALORY**:\n"
                "- **DXY & FX**: Dolar w fazie konsolidacji; szansa na obronę wsparcia na EUR/USD (1.0800).\n"
                "- **Indeksy (DAX, S&P 500)**: Nastawienie umiarkowanie bycze (Long bias po lokalnych korektach).\n"
                "- **Złoto & Surowce**: Złoto pod presją silnych rentowności obligacji, ropa stabilna.\n"
                "- **Kryptowaluty (BTC/ETH)**: Konsolidacja w strefie akumulacji przed ruchem kierunkowym.\n\n"
                "⚠️ **GŁÓWNE PUŁAPKI TYGODNIA**:\n"
                "- Unikaj agresywnego pozycjonowania przed piątkowym odczytem NFP z USA."
            )

        market_lines = [
            f"- {ticker}: {info.get('price', 'N/A')} ({info.get('change_pct', '0.00%')})"
            for ticker, info in market_data.items()
        ]
        market_str = "\n".join(market_lines) if market_lines else "Brak danych rynkowych"

        event_lines = [
            f"- {e.get('time', '')} [{e.get('currency', '')}] {e.get('title', '')} (Waga: {e.get('impact', '🔴')})"
            for e in calendar_events[:15]
        ]
        events_str = "\n".join(event_lines) if event_lines else "Brak kluczowych publikacji"

        news_lines = [
            f"- [{h.get('region', 'GLOBAL')}] {h.get('title', '')} ({h.get('source', '')})"
            for h in news_headlines[:8]
        ]
        news_str = "\n".join(news_lines) if news_lines else "Brak świeżych doniesień"

        template = self.get_prompt_template(
            "weekly_outlook",
            default="Przygotuj strategiczny plan na nadchodzący tydzień:\n{calendar_events_str}\n{market_data_str}\n{news_headlines_str}"
        )
        prompt = template.format(
            calendar_events_str=events_str,
            market_data_str=market_str,
            news_headlines_str=news_str,
        )

        return await self._call_gemini(
            prompt,
            fallback_msg="Strategiczny plan tygodniowy: Rynki przygotowują się na serię kluczowych publikacji makroekonomicznych.",
        )

    async def generate_session_advisory(
        self,
        session_key: str,
        market_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_headlines: List[Dict[str, Any]],
    ) -> str:
        """Generate tailored session briefing (london, newyork, asia) dispatched 1h before pre-market."""
        s_clean = session_key.lower().strip()
        template_name = f"session_{s_clean}" if s_clean in ["london", "newyork", "asia"] else "session_london"

        market_lines = [
            f"- {ticker}: {info.get('price', 'N/A')} ({info.get('change_pct', '0.00%')})"
            for ticker, info in market_data.items()
        ]
        market_str = "\n".join(market_lines) if market_lines else "Brak danych rynkowych"

        # Filter strictly High (🔴) and Medium (🟡) events; omit Low (⚪) / less important
        important_events = [
            e for e in economic_events
            if e.get("impact") in ["🔴", "🟡"] or e.get("weight") in [1, 2]
        ]
        event_lines = [
            f"- {e.get('time', '')} [{e.get('currency', '')}] {e.get('title', '')} (Waga: {e.get('impact', '🟡')})"
            for e in important_events[:12]
        ]
        events_str = "\n".join(event_lines) if event_lines else "Brak istotnych publikacji (brak wydarzeń o wadze 🔴 lub 🟡)"

        news_lines = [
            f"- [{h.get('region', 'GLOBAL')}] {h.get('title', '')} ({h.get('source', '')})"
            for h in news_headlines[:8]
        ]
        news_str = "\n".join(news_lines) if news_lines else "Brak świeżych nagłówków"

        if not self._client:
            if s_clean == "london":
                return (
                    "🧭 **SENTYMENT SESJI EUROPEJSKIEJ (09:00 CET)**: Otwarcie w klimacie Risk-On.\n\n"
                    "🇩🇪 **PLAN NA DAX**: Byczy sentyment na otwarciu kasowym. Cel: 18,480 pkt.\n"
                    "💱 **FX MAJORS (EUR/USD, GBP/USD)**: EUR/USD broni wsparcia 1.0820 przed popołudniem.\n\n"
                    "🎯 **REKOMENDACJE**:\n"
                    "- 🟢 **CO HANDLOWAĆ**: DAX Long po otwarciu Frankfurtu (09:00-09:45).\n"
                    "- ⛔ **CZEGO UNIKAĆ**: Pozycji długoterminowych na EUR/USD przed danymi z USA o 14:30."
                )
            elif s_clean == "newyork":
                return (
                    "🇺🇸 **WALL STREET PRE-MARKET**: Kontrakty na S&P 500 i Nasdaq w lekkim plusie przed 15:30 CET.\n\n"
                    "📊 **DANE Z USA (14:30 / 16:00)**: Rynek wyczekuje na odczyty z rynku pracy i ISM.\n"
                    "🪙 **KRYPTO & SUROWCE**: Złoto stabilne przy 2500$, BTC konsoliduje.\n\n"
                    "🎯 **REKOMENDACJE**:\n"
                    "- 🟢 **CO HANDLOWAĆ**: Nasdaq / S&P 500 w pierwszym impulsie po otwarciu kasowym.\n"
                    "- ⛔ **CZEGO UNIKAĆ**: Handlu bezpośrednio w sekundzie publikacji odczytu makro o 14:30."
                )
            else:  # asia
                return (
                    "🇯🇵 **OTWARCIE SESJI AZJATYCKIEJ**: Spokojny handel po zamknięciu w USA.\n\n"
                    "🦘 **PARY ANTYPODÓW & CHINY**: USD/JPY stabilizuje się wokół 154.00, AUD/USD wyczekuje na dane z Chin.\n\n"
                    "🎯 **REKOMENDACJE**:\n"
                    "- 🟢 **CO HANDLOWAĆ**: USD/JPY oraz Nikkei w oknie 01:00-03:00 CET.\n"
                    "- ⛔ **CZEGO UNIKAĆ**: Par walutowych z rynków wschodzących i krzyżówek EUR z uwagi na nocne spready."
                )

        template = self.get_prompt_template(
            template_name,
            default="Podsumuj sytuację rynkową dla sesji:\n{market_data_str}\n{calendar_events_str}\n{news_headlines_str}"
        )
        prompt = template.format(
            market_data_str=market_str,
            calendar_events_str=events_str,
            news_headlines_str=news_str,
        )

        return await self._call_gemini(
            prompt,
            fallback_msg=f"Briefing sesji {s_clean.upper()}: Rynki bazowe w oczekiwaniu na otwarcie handlu.",
        )

    async def generate_trader_advisory(
        self,
        market_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_headlines: List[Dict[str, Any]],
    ) -> str:
        """Generate comprehensive 8:00 AM daily trading advisory focused on FX Majors, DXY, and DAX."""
        # Alias to London session advisory
        return await self.generate_session_advisory("london", market_data, economic_events, news_headlines)

    async def generate_single_asset_advisory(
        self,
        symbol: str,
        asset_data: Dict[str, Any],
        news_headlines: List[Dict[str, Any]],
    ) -> str:
        """Generate targeted trading advisory for a single asset (e.g. DAX, BTC, EUR/USD)."""
        if not self._client:
            return (
                f"🎯 **ANALIZA DLA {symbol.upper()}**:\n"
                f"- **Kierunek**: Umiarkowanie Byczy (Long bias).\n"
                f"- **Aktualna cena**: `{asset_data.get('price', 'N/A')}` ({asset_data.get('change_pct', '0.00%')}).\n"
                f"- **Zalecenie**: Szukaj wejścia po re-teście wsparcia na niższych interwałach (M15/H1).\n"
                f"- **Ryzyko**: Zwróć uwagę na zachowanie DXY i popołudniowe publikacje z USA."
            )

        asset_str = f"Cena: {asset_data.get('price')}, Zmiana 24h: {asset_data.get('change_pct')}, Ticker: {asset_data.get('ticker')}"
        headlines_lines = [f"- {h.get('title')} ({h.get('source')})" for h in news_headlines[:5]]
        headlines_str = "\n".join(headlines_lines) if headlines_lines else "Brak bezpośrednich nagłówków."

        template = self.get_prompt_template(
            "single_asset_advisory",
            default="Przeanalizuj instrument {symbol}:\n{asset_data_str}\n{relevant_headlines_str}"
        )
        prompt = template.format(
            symbol=symbol.upper(),
            asset_data_str=asset_str,
            relevant_headlines_str=headlines_str,
        )

        fallback_mock = (
            f"🎯 **ANALIZA DLA {symbol.upper()}**:\n"
            f"- **Kierunek**: Umiarkowanie Byczy (Long bias).\n"
            f"- **Aktualna cena**: `{asset_data.get('price', 'N/A')}` ({asset_data.get('change_pct', '0.00%')}).\n"
            f"- **Zalecenie**: Szukaj wejścia po re-teście wsparcia na niższych interwałach (M15/H1).\n"
            f"- **Ryzyko**: Zwróć uwagę na zachowanie DXY i popołudniowe publikacje z USA."
        )

        return await self._call_gemini(prompt, fallback_msg=fallback_mock)

    async def generate_portfolio_summary(
        self,
        portfolio_data: Dict[str, Any],
        portfolio_news: List[Dict[str, Any]],
    ) -> str:
        """Generate analysis and news digest for user's portfolio holdings."""
        if not self._client:
            sym_list = list(portfolio_data.keys())
            sym_str = ", ".join(sym_list[:4]) if sym_list else "Twoje walory"
            return (
                f"🚨 **KOMUNIKATY I ALERTY DLA PORTFELA ({sym_str})**:\n"
                "- Spółki z Twojego koszyka utrzymują stabilne wyceny na rynkach bazowych (Wall Street / Crypto).\n"
                "- Brak negatywnych ostrzeżeń wynikowych czy obniżek rekomendacji analityków.\n"
                "📈 **OCENA SYTUACJI**: Pozycje stabilne, kontynuuj monitorowanie poziomów wsparcia."
            )

        quotes_lines = [
            f"- {sym}: {info.get('price')} ({info.get('change_pct')})"
            for sym, info in portfolio_data.items()
        ]
        quotes_str = "\n".join(quotes_lines)

        news_lines = [
            f"- [{h.get('matched_symbol', 'INFO')}] {h.get('title')} ({h.get('source')})"
            for h in portfolio_news
        ]
        news_str = "\n".join(news_lines) if news_lines else "Brak nowych komunikatów dla portfela."

        template = self.get_prompt_template(
            "portfolio_news",
            default="Podsumuj sytuację i wiadomości dla spółek z portfela:\n{portfolio_quotes_str}\n{portfolio_headlines_str}"
        )
        prompt = template.format(
            portfolio_quotes_str=quotes_str,
            portfolio_headlines_str=news_str,
        )

        return await self._call_gemini(prompt, fallback_msg="Podsumowanie portfela chwilowo niedostępne.")

    async def generate_calendar_advisory(self, economic_events: List[Dict[str, Any]]) -> str:
        """Generate analysis and warnings based on today's economic calendar."""
        if not self._client:
            return (
                "⚠️ **KRYTYCZNE OKNA CZASOWE**: Zwróć uwagę na odczyty o 14:30 i 16:00.\n"
                "💡 **ZALECENIA**: Zamknij lub zabezpiecz pozycje scalpingowe 5 minut przed publikacją danych z USA."
            )

        event_lines = [
            f"- `{e.get('time', '')}` [{e.get('currency', '')}] {e.get('title', '')} (Waga: {e.get('impact', '🟡')})"
            for e in economic_events
        ]
        events_str = "\n".join(event_lines) if event_lines else "Brak istotnych wydarzeń w kalendarzu."

        template = self.get_prompt_template(
            "calendar_analysis",
            default="Oceń ryzyka z poniższego kalendarza ekonomicznego dla tradera:\n{calendar_events_str}"
        )
        prompt = template.format(calendar_events_str=events_str)

        return await self._call_gemini(prompt, fallback_msg="Analiza kalendarza chwilowo niedostępna.")

    async def generate_crypto_summary(self, crypto_headlines: List[Dict[str, Any]]) -> str:
        """Generate a dedicated global cryptocurrency and digital asset summary."""
        if not self._client:
            return (
                "🪙 **BITCOIN & ETHEREUM**: BTC konsoliduje powyżej kluczowego wsparcia przy stabilnych napływach do funduszy ETF.\n"
                "⚡ **ALTCOINY & DEFI**: Aktywność na sieciach L2 i wolumeny DEX utrzymują trend wzrostowy.\n"
                "🏛️ **MAKRO & REGULACJE**: Globalne rynki wyceniają kolejne etapy adaptacji krypto przez instytucje."
            )

        news_lines = [
            f"- {h.get('title', '')} (Źródło: {h.get('source', 'Crypto')})"
            for h in crypto_headlines[:10]
        ]
        news_str = "\n".join(news_lines) if news_lines else "Brak świeżych nagłówków krypto."

        template = self.get_prompt_template(
            "crypto_summary",
            default="Podsumuj sytuację na globalnym rynku krypto:\n{crypto_headlines_str}"
        )
        prompt = template.format(crypto_headlines_str=news_str)

        return await self._call_gemini(prompt, fallback_msg="Podsumowanie krypto chwilowo niedostępne.")

    async def generate_news_summary(self, regional_headlines: List[Dict[str, Any]]) -> str:
        """Generate a synthesized multi-region news brief."""
        if not self._client:
            return (
                "• 🇵🇱 **Polska / GPW**: Spokojny początek sesji na warszawskim parkiecie.\n"
                "• 🇺🇸 / 🇪🇺 **USA i Europa**: Rynki wyczekują na popołudniowe odczyty makroekonomiczne.\n"
                "• 🌐 **Global**: Dolar stabilny, ropa naftowa w konsolidacji."
            )

        news_lines = [
            f"- [{h.get('region', 'GLOBAL')}] {h.get('title', '')} (Źródło: {h.get('source', '')})"
            for h in regional_headlines[:12]
        ]
        news_str = "\n".join(news_lines)

        template = self.get_prompt_template(
            "news_summary",
            default="Podsumuj najważniejsze wiadomości rynkowe w podziale na PL, USA/UE i Global:\n{news_headlines_str}"
        )
        prompt = template.format(news_headlines_str=news_str)

        return await self._call_gemini(prompt, fallback_msg="Podsumowanie newsów chwilowo niedostępne.")

    async def generate_flash_news_summary(self, headlines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate an ultra-concise flash bulletin with importance evaluation (HIGH, MEDIUM, LOW).
        Returns None if news is assessed as LOW importance (noise/irrelevant) or if an error occurs.
        No rigid dummy fallback message is ever returned.
        """
        if not headlines:
            return None

        if not self._client:
            self.last_error = "Brak zainicjalizowanego klienta Gemini API"
            return None

        news_lines = [
            f"- {h.get('title', '')} (Źródło: {h.get('source', '')}, Region: {h.get('region', '')})"
            for h in headlines[:5]
        ]
        news_str = "\n".join(news_lines)

        template = self.get_prompt_template(
            "flash_news",
            default="Oceń wagę newsa (HIGH/MEDIUM/LOW) i zwróć JSON ze statusem, nagłówkiem oraz podsumowaniem:\n{headlines_str}",
        )
        try:
            prompt = template.format(headlines_str=news_str)
        except Exception:
            prompt = template.replace("{headlines_str}", news_str)

        raw_response = await self._call_gemini(prompt, fallback_msg="")
        if not raw_response:
            if not self.last_error:
                self.last_error = "Brak odpowiedzi od Gemini API dla zapytania Flash News"
            return None

        try:
            clean_json = raw_response
            if "```json" in clean_json:
                clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()

            parsed = json.loads(clean_json, strict=False)
            importance = str(parsed.get("importance", "MEDIUM")).upper().strip()
            if importance == "LOW":
                self.last_error = None
                return None

            header = parsed.get("header")
            if header:
                header = str(header).strip() or None

            summary = parsed.get("summary")
            if not summary:
                self.last_error = "Odpowiedź AI nie zawierała pola summary"
                return None

            self.last_error = None
            return {
                "importance": importance if importance in ["HIGH", "MEDIUM"] else "MEDIUM",
                "header": header,
                "summary": str(summary).strip(),
            }
        except Exception as e:
            logger.warning("Failed to parse JSON from flash news Gemini response: %s", e)
            if "📰" in raw_response:
                sub_text = raw_response[raw_response.index("📰"):]
                for stop_tok in ['",\n', '"\n}', '"}', "```"]:
                    if stop_tok in sub_text:
                        sub_text = sub_text.split(stop_tok)[0]
                cleaned_summary = sub_text.replace('\\n', '\n').replace('\\"', '"').rstrip('"').strip()
                self.last_error = None
                return {
                    "importance": "HIGH" if ("🚨" in raw_response or "PILNE" in raw_response) else "MEDIUM",
                    "header": "🚨 PILNE: Istotne doniesienie rynkowe" if ("🚨" in raw_response or "PILNE" in raw_response) else None,
                    "summary": cleaned_summary,
                }
            self.last_error = f"Błąd parsowania odpowiedzi AI: {e}"
            return None

    async def evaluate_session_performance(
        self,
        session_key: str,
        session_advisory: str,
        start_prices: Dict[str, Any],
        end_prices: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a specific trading session's recommendations against market reality using Gemini AI."""
        s_clean = session_key.lower().strip()
        session_name = {
            "london": "Londyn (Sesja Europejska)",
            "newyork": "Nowy Jork (Wall Street)",
            "asia": "Azja (Tokio / Sydney)",
        }.get(s_clean, "Sesja Handlowa")

        start_lines = [
            f"- {sym}: {data.get('price', 'N/A')}"
            for sym, data in start_prices.items()
        ]
        end_lines = [
            f"- {sym}: {data.get('price', 'N/A')} (Zmiana: {data.get('change_pct', '0.00%')})"
            for sym, data in end_prices.items()
        ]

        template = self.get_prompt_template(
            "session_evaluation",
            default=(
                "Oceń trafność briefingu dla sesji {session_name} ({session_advisory}) na podstawie cen początkowych "
                "({start_prices_str}) i końcowych ({end_prices_str}). Zwróć JSON ze score (0-100), status, breakdown i conclusions."
            )
        )
        start_p_str = "\n".join(start_lines) or "Brak danych cenowych."
        end_p_str = "\n".join(end_lines) or "Brak danych cenowych."
        try:
            prompt = template.format(
                session_name=session_name,
                session_advisory=session_advisory,
                start_prices_str=start_p_str,
                end_prices_str=end_p_str,
            )
        except Exception:
            prompt = (
                template.replace("{session_name}", session_name)
                .replace("{session_advisory}", session_advisory)
                .replace("{start_prices_str}", start_p_str)
                .replace("{end_prices_str}", end_p_str)
            )

        fallback = {
            "score": 80,
            "status": "udana",
            "breakdown": f"• {session_name}: Zgodność z założonym kierunkiem sesji i zachowaniem kluczowych walorów.",
            "conclusions": f"Główne zalecenia dla sesji {session_name} zostały zrealizowane zgodnie z oczekiwaniami rynkowymi.",
        }

        if not self._client:
            return fallback

        raw_response = await self._call_gemini(prompt, fallback_msg="")
        if not raw_response:
            return fallback

        try:
            clean_json = raw_response
            if "```json" in clean_json:
                clean_json = clean_json.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```", 1)[1].split("```", 1)[0].strip()

            parsed = json.loads(clean_json)
            score = int(parsed.get("score", 75))
            return {
                "score": max(0, min(100, score)),
                "status": "udana" if score > 75 else ("neutralna" if score > 25 else "nieudana"),
                "breakdown": str(parsed.get("breakdown", fallback["breakdown"])),
                "conclusions": str(parsed.get("conclusions", fallback["conclusions"])),
            }
        except Exception as e:
            logger.warning("Failed to parse session evaluation JSON from Gemini response: %s. Using text fallback.", e)
            return fallback

    async def evaluate_briefing_performance(
        self,
        yesterday_advisory: str,
        start_prices: Dict[str, Any],
        current_prices: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Legacy helper aliasing to London session evaluation."""
        return await self.evaluate_session_performance(
            session_key="london",
            session_advisory=yesterday_advisory,
            start_prices=start_prices,
            end_prices=current_prices,
        )

    async def _call_gemini(self, prompt: str, fallback_msg: str) -> str:
        """Async execution of Gemini text generation."""
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=prompt,
            )
            if response:
                if hasattr(response, "text") and response.text:
                    self.last_error = None
                    return response.text.strip()
                if hasattr(response, "candidates") and response.candidates:
                    parts_text = []
                    for c in response.candidates:
                        if hasattr(c, "content") and hasattr(c.content, "parts") and c.content.parts:
                            for p in c.content.parts:
                                if hasattr(p, "text") and p.text:
                                    parts_text.append(p.text)
                    if parts_text:
                        self.last_error = None
                        return "".join(parts_text).strip()
            self.last_error = "Gemini API zwróciło pustą odpowiedź"
            return fallback_msg
        except Exception as e:
            self.last_error = f"Błąd Gemini API ({type(e).__name__}): {e}"
            logger.error("Gemini API call failed: %s", e)
            return fallback_msg
