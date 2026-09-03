"""Admin Cog - handles diagnostics, bot status, we.trade community info, and live prompt reloading."""

import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.utils.embeds import BRAND_FOOTER
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class AdminCog(commands.Cog, name="Admin"):
    """Administrative, diagnostic, community, and hot-reload commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Sprawdź opóźnienie i połączenie bota z Discordem."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 **Pong!** Opóźnienie: `{latency_ms}ms`")

    @commands.command(name="wetrade", aliases=["about", "spolecznosc", "info"])
    async def wetrade_command(self, ctx: commands.Context) -> None:
        """Informacje o społeczności we.trade i funkcjach bota Newsbox."""
        from newsbox.utils.embeds import send_full_message
        msg = (
            "## 🌐 Społeczność we.trade & Newsbox Bot\n"
            "> **Newsbox** to zaawansowany asystent rynkowy AI stworzony dla członków społeczności **we.trade**.\n"
            "> Dostarcza traderom przewagę rynkową dzięki zautomatyzowanym raportom makro, analizom sentymentu AI oraz trackingowi skuteczności.\n\n"
            "### 💎 Główne Moduły i Komendy\n"
            "• `!briefing` — Raport makro dla nadchodzącej sesji (`!london`, `!ny`, `!asia`)\n"
            "• `!weekly` — Niedzielny horyzont strategiczny na cały tydzień (10:00)\n"
            "• `!flash` — Flash News ze świata i doniesienia rynkowe na żywo (:25, :55)\n"
            "• `!calendar` — 24-godzinny kalendarz ekonomiczny z oceną ryzyk AI\n"
            "• `!accuracy` — Wielopoziomowy ranking skuteczności analiz AI\n"
            "• `!portfolio` — Monitoring i wiadomości spółek z Twojego portfela\n"
            "• `!news` — Przegląd wiadomości ze świata, USA, Polski i krypto\n\n"
            f"-# 🏛️ Społeczność: **we.trade** • 🔒 Dostęp VIP: `{self.settings.vip_role_name}`"
        )
        await send_full_message(ctx.channel, msg)

    @commands.command(name="status")
    async def status(self, ctx: commands.Context) -> None:
        """Wyświetl aktualny stan techniczny bota i aktywne instrumenty."""
        from newsbox.utils.embeds import send_full_message
        tickers_str = ", ".join([f"**{k}** (`{v}`)" for k, v in self.settings.tickers.items()])
        msg = (
            "## 🤖 Newsbox Bot Status • we.trade\n"
            "> Inteligentny bot analityczny dla społeczności inwestorów i traderów **we.trade**.\n\n"
            "### ⚙️ Konfiguracja Systemowa\n"
            f"• **Środowisko:** `{self.settings.environment}`\n"
            f"• **Model AI:** `{self.settings.gemini_model}`\n"
            f"• **Harmonogram Sesji:** Londyn `07:00` • Nowy Jork `13:30` • Azja `23:00` (CET)\n"
            f"• **Harmonogram Flash:** `:25` oraz `:55` w każdej godzinie\n"
            f"• **Wymagana Rola VIP:** `{self.settings.vip_role_name}`\n\n"
            f"### 📈 Śledzone Aktywa Bazowe\n{tickers_str or 'Brak'}\n\n"
            f"-# {BRAND_FOOTER}"
        )
        await send_full_message(ctx.channel, msg)

    @commands.command(name="reload_prompts", aliases=["przeladuj_prompty"])
    @commands.has_permissions(administrator=True)
    async def reload_prompts(self, ctx: commands.Context) -> None:
        """Przeładuj na gorąco szablony promptów z folderu prompts/ bez restartu bota."""
        briefings_cog = self.bot.get_cog("Briefings & Trader Advisory")
        news_cog = self.bot.get_cog("News Feed")

        reloaded = 0
        if briefings_cog and hasattr(briefings_cog, "gemini_service"):
            briefings_cog.gemini_service.load_prompts()
            reloaded += len(briefings_cog.gemini_service._prompt_cache)

        if news_cog and hasattr(news_cog, "gemini_service"):
            news_cog.gemini_service.load_prompts()

        await ctx.send(f"✅ Przeładowano szablony promptów z `{self.settings.prompts_dir}/`. Załadowano: **{reloaded}** szablonów.")
        logger.info("Prompts reloaded by %s", ctx.author)


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(AdminCog(bot))
