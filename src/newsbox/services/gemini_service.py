"""Gemini AI Service for generating macro summaries, trader advisory, single-asset briefs, and portfolio insights."""

from __future__ import annotations

import asyncio
from pathlib import Path
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
        self._initialize_client()
        self.load_prompts()

    def _initialize_client(self) -> None:
        """Initialize Google GenAI client if api_key is present."""
        if not self.api_key:
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

    async def generate_trader_advisory(
        self,
        market_data: Dict[str, Any],
        economic_events: List[Dict[str, Any]],
        news_headlines: List[Dict[str, Any]],
    ) -> str:
        """Generate comprehensive 8:00 AM daily trading advisory focused on FX Majors, DXY, and DAX."""
        if not self._client:
            return (
                "🧭 **MARKET REGIME & MAKRO BIAS**: Umiarkowany Risk-On przy konsolidacji DXY wokół 104.20.\n\n"
                "💱 **FX MAJORS & DXY**:\n"
                "- **EUR/USD**: Spokojny handel przed popołudniowymi odczytami z USA. Wsparcie na 1.0820.\n"
                "- **USD/JPY**: Presja wzrostowa podtrzymana przez rentowności obligacji USA.\n\n"
                "🇩🇪 **DAX & EUROPEAN EQUITIES**:\n"
                "- Pozytywne otwarcie kasowe o 09:00. Cel kupujących: 18,480 pkt.\n\n"
                "🟢 **CO MOŻNA DZISIAJ HANDLOWAĆ (IN PLAY)**:\n"
                "- **DAX (Long)**: Wybicie lokalnego oporu na otwarciu sesji we Frankfurcie.\n"
                "- **BTC**: Utrzymanie strefy popytowej, perspektywa testu 68k$.\n\n"
                "⛔ **CZEGO DZISIAJ NIE HANDLOWAĆ (NO-TRADE)**:\n"
                "- **EUR/USD & Pary USD**: Unikaj pozycji intraday w oknie 14:25-14:40 z uwagi na odczyty makro.\n\n"
                "📋 **PLAN SESJI & WSKAZÓWKI**:\n"
                "- Handluj pierwsze 45 minut po otwarciu 09:00, następnie zredukuj ryzyko przed danymi z USA o 14:30."
            )

        market_lines = [
            f"- {ticker}: {info.get('price', 'N/A')} ({info.get('change_pct', '0.00%')})"
            for ticker, info in market_data.items()
        ]
        market_str = "\n".join(market_lines) if market_lines else "Brak danych rynkowych"

        event_lines = [
            f"- {e.get('time', '')} [{e.get('currency', '')}] {e.get('title', '')} (Waga: {e.get('impact', '🟡')})"
            for e in economic_events[:8]
        ]
        events_str = "\n".join(event_lines) if event_lines else "Brak kluczowych publikacji dzisiaj"

        news_lines = [
            f"- [{h.get('region', 'GLOBAL')}] {h.get('title', '')} ({h.get('source', '')})"
            for h in news_headlines[:8]
        ]
        news_str = "\n".join(news_lines) if news_lines else "Brak świeżych nagłówków"

        template = self.get_prompt_template(
            "trader_advisory",
            default="Podsumuj sytuację rynkową z naciskiem na FX Majors, DXY i DAX:\n{market_data_str}\n{calendar_events_str}\n{news_headlines_str}"
        )

        prompt = template.format(
            market_data_str=market_str,
            calendar_events_str=events_str,
            news_headlines_str=news_str,
        )

        return await self._call_gemini(prompt, fallback_msg="Nie udało się wygenerować rekomendacji AI.")

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

    async def evaluate_briefing_performance(
        self,
        yesterday_advisory: str,
        start_prices: Dict[str, Any],
        current_prices: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate yesterday's recommendations against market reality using Gemini AI."""
        start_lines = [
            f"- {sym}: {data.get('price', 'N/A')}"
            for sym, data in start_prices.items()
        ]
        current_lines = [
            f"- {sym}: {data.get('price', 'N/A')} (24h Zmiana: {data.get('change_pct', '0.00%')})"
            for sym, data in current_prices.items()
        ]

        template = self.get_prompt_template(
            "briefing_evaluation",
            default=(
                "Oceń trafność wczorajszego briefingu ({yesterday_advisory}) na podstawie cen początkowych "
                "({start_prices_str}) i obecnych ({current_prices_str}). Zwróć JSON ze score (0-100), status, breakdown i conclusions."
            )
        )
        prompt = template.format(
            yesterday_advisory=yesterday_advisory,
            start_prices_str="\n".join(start_lines) or "Brak danych cenowych.",
            current_prices_str="\n".join(current_lines) or "Brak danych cenowych.",
        )

        fallback = {
            "score": 80,
            "status": "udana",
            "breakdown": "• DAX / Rynki UE: Zgodność z założonym kierunkiem sesji.\n• FX Majors: Stabilizacja zmienności w wyznaczonych strefach.",
            "conclusions": "Główne założenia z porannego briefu zostały zrealizowane bez nieoczekiwanych zwrotów akcji na rynkach bazowych.",
        }

        if not self._client:
            return fallback

        raw_response = await self._call_gemini(prompt, fallback_msg="")
        if not raw_response:
            return fallback

        try:
            # Extract JSON substring if wrapped in markdown blocks
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
            logger.warning("Failed to parse evaluation JSON from Gemini response: %s. Using text fallback.", e)
            return fallback

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
                    return response.text.strip()
                if hasattr(response, "candidates") and response.candidates:
                    parts_text = []
                    for c in response.candidates:
                        if hasattr(c, "content") and hasattr(c.content, "parts") and c.content.parts:
                            for p in c.content.parts:
                                if hasattr(p, "text") and p.text:
                                    parts_text.append(p.text)
                    if parts_text:
                        return "".join(parts_text).strip()
            return fallback_msg
        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            return fallback_msg
