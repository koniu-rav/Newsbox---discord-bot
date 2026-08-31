"""Admin Cog - handles diagnostics, bot status, and live prompt reloading."""

import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class AdminCog(commands.Cog, name="Admin"):
    """Administrative, diagnostic, and hot-reload commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Sprawdź opóźnienie i połączenie bota z Discordem."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 **Pong!** Opóźnienie: `{latency_ms}ms`")

    @commands.command(name="status")
    async def status(self, ctx: commands.Context) -> None:
        """Wyświetl aktualny stan techniczny bota i aktywne instrumenty."""
        embed = discord.Embed(
            title="🤖 Newsbox Bot Status",
            color=0x43A047,
        )
        embed.add_field(name="Środowisko", value=f"`{self.settings.environment}`", inline=True)
        embed.add_field(name="Model AI", value=f"`{self.settings.gemini_model}`", inline=True)
        embed.add_field(
            name="Czas Briefingu",
            value=f"`{self.settings.briefing_time}` ({self.settings.briefing_timezone})",
            inline=True,
        )

        # Active tickers
        tickers_str = ", ".join([f"**{k}** (`{v}`)" for k, v in self.settings.tickers.items()])
        embed.add_field(name="📈 Śledzone Aktywa", value=tickers_str or "Brak", inline=False)

        embed.set_footer(text="Newsbox Health & Diagnostic System")
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
