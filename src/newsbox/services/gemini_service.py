"""Gemini AI Service for generating macro summaries, trader advisory, and calendar insights."""

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
        self.api_key = api_key or self.settings.gemini_api_key
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
        """Generate comprehensive 8:00 AM daily trading advisory with Do's and Don'ts."""
        if not self._client:
            return (
                "🧭 **MARKET REGIME & BIAS**: Umiarkowany Risk-On przy stabilizacji DXY.\n\n"
                "🟢 **CO MOŻNA DZISIAJ HANDLOWAĆ (IN PLAY)**:\n"
                "- **DAX / Indeksy UE**: Pozytywny sentyment po otwarciu sesji europejskiej.\n"
                "- **BTC**: Utrzymanie kluczowego wsparcia, kontynuacja trendu wzrostowego.\n\n"
                "⛔ **CZEGO DZISIAJ NIE HANDLOWAĆ (NO-TRADE)**:\n"
                "- **EUR/USD & Pary z USD**: Unikaj agresywnych pozycji intraday przed publikacją danych o 14:30.\n\n"
                "📋 **PLAN SESJI & WSKAZÓWKI**:\n"
                "- Zachowaj ostrożność w oknie 14:30-16:00. Zmniejsz wielkość pozycji przed odczytami makro."
            )

        # Format inputs
        market_lines = [
            f"- {ticker}: {info.get('price', 'N/A')} ({info.get('change_pct', '0.00%')})"
            for ticker, info in market_data.items()
        ]
        market_str = "\n".join(market_lines) if market_lines else "Brak danych rynkowych"

        event_lines = [
            f"- {e.get('time', '')} [{e.get('currency', '')}] {e.get('title', '')} (Wpływ: {e.get('impact', '🟡')})"
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
            default="Podsumuj sytuację rynkową i wskaż co handlować, a czego unikać dzisiaj:\n{market_data_str}\n{calendar_events_str}\n{news_headlines_str}"
        )

        prompt = template.format(
            market_data_str=market_str,
            calendar_events_str=events_str,
            news_headlines_str=news_str,
        )

        return await self._call_gemini(prompt, fallback_msg="Nie udało się wygenerować rekomendacji AI.")

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

    async def _call_gemini(self, prompt: str, fallback_msg: str) -> str:
        """Async execution of Gemini text generation."""
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model_name,
                contents=prompt,
            )
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return fallback_msg
        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            return fallback_msg
