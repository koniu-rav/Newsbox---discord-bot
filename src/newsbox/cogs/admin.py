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
        embed = discord.Embed(
            title="🌐 Społeczność we.trade & Newsbox Bot",
            description=(
                "**Newsbox** to zaawansowany asystent rynkowy AI stworzony dla członków społeczności **we.trade**.\n\n"
                "🎯 **Misja we.trade**:\n"
                "Dostarczanie traderom i inwestorom bezkompromisowej przewagi rynkowej dzięki zautomatyzowanym "
                "raportom makroekonomicznym, analizom sentymentu AI oraz precyzyjnemu trackingowi skuteczności zaleceń.\n\n"
                "💎 **Główne moduły**:\n"
                "• `!briefing` — Poranny brief makro (FX Majors, DXY, DAX) o 08:00\n"
                "• `!accuracy` — Codzienna ewaluacja trafności AI o 12:30\n"
                "• `!portfolio` — Monitoring wycen i wiadomości Twoich spółek z Wall Street & Krypto\n"
                "• `!calendar` — Kalendarz ekonomiczny z oceną ryzyk sesyjnych\n"
                "• `!crypto` — Dedykowany strumień wiadomości ze świata krypto"
            ),
            color=0x1ABC9C,
        )
        embed.add_field(name="🏛️ Społeczność", value="**we.trade**", inline=True)
        embed.add_field(name="🔒 Dostęp VIP", value=f"Rola `{self.settings.vip_role_name}`", inline=True)
        embed.set_footer(text=BRAND_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="status")
    async def status(self, ctx: commands.Context) -> None:
        """Wyświetl aktualny stan techniczny bota i aktywne instrumenty."""
        embed = discord.Embed(
            title="🤖 Newsbox Bot Status • we.trade",
            description="Inteligentny bot analityczny dla społeczności **we.trade**.",
            color=0x43A047,
        )
        embed.add_field(name="Społeczność", value="**we.trade**", inline=True)
        embed.add_field(name="Środowisko", value=f"`{self.settings.environment}`", inline=True)
        embed.add_field(name="Model AI", value=f"`{self.settings.gemini_model}`", inline=True)
        embed.add_field(
            name="Czas Briefingu",
            value=f"`{self.settings.briefing_time}` ({self.settings.briefing_timezone})",
            inline=True,
        )
        embed.add_field(name="Ewaluacja Accuracy", value=f"`{self.settings.accuracy_time}` (Mon-Fri)", inline=True)
        embed.add_field(name="Wymagana Rola", value=f"`{self.settings.vip_role_name}`", inline=True)

        # Active tickers
        tickers_str = ", ".join([f"**{k}** (`{v}`)" for k, v in self.settings.tickers.items()])
        embed.add_field(name="📈 Śledzone Aktywa", value=tickers_str or "Brak", inline=False)

        embed.set_footer(text=BRAND_FOOTER)
        await ctx.send(embed=embed)

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
