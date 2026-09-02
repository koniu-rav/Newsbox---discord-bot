"""News Cog - handles regional news commands (PL, USA, EU, Crypto, Global) and 30-minute flash news streaming."""

from datetime import datetime
import discord
from discord.ext import commands
from newsbox.config import get_settings
from newsbox.services.gemini_service import GeminiService
from newsbox.services.news_service import NewsService
from newsbox.utils.embeds import (
    create_crypto_news_embed,
    create_flash_news_embed,
    create_regional_news_embed,
)
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsCog(commands.Cog, name="News Feed"):
    """Commands for browsing business, stock market, crypto, and macroeconomic news."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = get_settings()
        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        self.last_flash_audit: Optional[Dict[str, Any]] = None

    async def compile_and_send_flash_news(
        self,
        channel: discord.abc.Messageable,
        is_manual: bool = False,
    ) -> None:
        """Fetch fresh breaking global headlines, evaluate importance, and send to Discord.
        If news is assessed as LOW importance, publication is skipped automatically.
        """
        try:
            from zoneinfo import ZoneInfo
            now_warsaw = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%H:%M:%S CET")

            # Check quiet window (market open: 08:50-09:15, 15:20-15:45)
            if not is_manual and self.news_service.is_in_quiet_window():
                logger.info("Skipping flash news dispatch: Market Open quiet window active.")
                self.last_flash_audit = {
                    "time": now_warsaw,
                    "headline": "Brak (okno otwarcia rynku)",
                    "importance": "SKIPPED",
                    "action": "⏸️ Pominięto: Trwa okno otwarcia sesji giełdowej (Market Open quiet window).",
                }
                return

            headlines = await self.news_service.fetch_flash_breaking_news(limit=2)
            if not headlines:
                logger.info("No fresh breaking news to dispatch for flash.")
                self.last_flash_audit = {
                    "time": now_warsaw,
                    "headline": "Brak nowych artykułów",
                    "importance": "NO_NEWS",
                    "action": "ℹ️ Pominięto: Brak świeżych, nieopublikowanych doniesień w tej chwili.",
                }
                if is_manual:
                    await channel.send("ℹ️ Brak świeżych, nieopublikowanych doniesień rynkowych w tej chwili.")
                return

            main_headline = headlines[0].get("title", "")
            main_source = headlines[0].get("source", "Global")

            flash_data = await self.gemini_service.generate_flash_news_summary(headlines)

            # Skip publication if news is unimportant / noise
            if not flash_data or flash_data.get("importance") == "LOW" or not flash_data.get("summary"):
                logger.info("Flash news skipped: AI evaluated '%s' as LOW importance / noise.", main_headline)
                self.last_flash_audit = {
                    "time": now_warsaw,
                    "headline": main_headline,
                    "source": main_source,
                    "importance": "LOW",
                    "action": "⚪ Pominięto: AI oceniło news jako nieważny / szum bez istotnego wpływu na rynki.",
                }
                if is_manual:
                    # For manual commands, send standard medium fallback
                    embed = create_flash_news_embed(
                        flash_summary=f"📰 {main_headline}.\n🎯 Brak bezpośredniego, gwałtownego wpływu na rynki bazowe.",
                        headlines=headlines,
                        importance="MEDIUM",
                    )
                    await channel.send(embed=embed)
                return

            importance = flash_data.get("importance", "MEDIUM")
            header = flash_data.get("header")

            self.last_flash_audit = {
                "time": now_warsaw,
                "headline": main_headline,
                "source": main_source,
                "importance": importance,
                "header": header,
                "action": f"{'🔴 Opublikowano (Alert PILNE)' if importance == 'HIGH' else '🔵 Opublikowano (Standardowy)'}",
            }

            embed = create_flash_news_embed(
                flash_summary=flash_data.get("summary", ""),
                headlines=headlines,
                header=header,
                importance=importance,
            )
            await channel.send(embed=embed)
            logger.info("Successfully dispatched flash news (importance=%s) to %s: %s", importance, channel, main_headline)
        except Exception as e:
            logger.error("Failed to dispatch flash news: %s", e, exc_info=True)

    @commands.command(name="news", aliases=["wiadomosci", "parkiet"])
    async def news_command(self, ctx: commands.Context, region: str = "ALL") -> None:
        """Pobierz najświeższe newsy biznesowe, giełdowe lub krypto.

        Użycie:
        - `!news` lub `!news all` - przegląd ze wszystkich rynków
        - `!news pl` - Polska (Parkiet, Bankier, GPW)
        - `!news us` / `!news usa` - Rynki USA & Wall Street
        - `!news eu` - Strefa Euro & EBC
        - `!news crypto` - Świat kryptowalut & blockchain (CoinDesk, Cointelegraph)
        - `!news global` - Rynki światowe, surowce i makro
        """
        async with ctx.typing():
            in_quiet = self.news_service.is_in_quiet_window()
            quiet_notice = (
                "\n*⏳ Uwaga: Trwa okno otwarcia sesji giełdowej (Market Open). Zmienność może być podwyższona.*"
                if in_quiet
                else ""
            )

            reg_normalized = region.upper()
            if reg_normalized in ["CRYPTO", "KRYPTO", "BTC"]:
                headlines = await self.news_service.fetch_crypto_news(limit=6)
                summary = await self.gemini_service.generate_crypto_summary(headlines)
                embed = create_crypto_news_embed(
                    headlines=headlines,
                    summary_text=summary + quiet_notice if summary else quiet_notice,
                )
                await ctx.send(embed=embed)
                return

            if reg_normalized in ["US", "USA"]:
                reg_key = "USA"
            elif reg_normalized in ["PL", "POLSKA", "GPW", "PARKIET"]:
                reg_key = "PL"
            elif reg_normalized in ["EU", "EUROPA"]:
                reg_key = "EU"
            elif reg_normalized in ["GLOBAL", "SWIAT"]:
                reg_key = "GLOBAL"
            else:
                reg_key = "ALL"

            headlines = await self.news_service.fetch_regional_news(reg_key, limit=6)
            summary = await self.gemini_service.generate_news_summary(headlines)

            embed = create_regional_news_embed(
                region=reg_key,
                headlines=headlines,
                summary_text=summary + quiet_notice if summary else quiet_notice,
            )
            await ctx.send(embed=embed)

    @commands.command(name="flash", aliases=["flashnews", "migawka"])
    async def flash_command(self, ctx: commands.Context, sub_arg: Optional[str] = None) -> None:
        """Ręcznie wygeneruj natychmiastową migawkę Flash News lub sprawdź status ostatniej oceny AI (`!flash status`)."""
        if sub_arg and sub_arg.lower().strip() in ["status", "log", "debug", "check"]:
            if not self.last_flash_audit:
                await ctx.send("ℹ️ Bot nie przeprowadził jeszcze żadnej automatycznej oceny Flash News od ostatniego restartu.")
                return

            embed = discord.Embed(
                title="🔍 Status Ostatniej Oceny Flash News • AI Audit",
                color=0x3498DB,
            )
            embed.add_field(name="⏰ Czas sprawdzenia", value=f"`{self.last_flash_audit.get('time', 'N/A')}`", inline=True)
            embed.add_field(name="🏷️ Ocena Wagi AI", value=f"`{self.last_flash_audit.get('importance', 'N/A')}`", inline=True)
            embed.add_field(name="📰 Sprawdzony Nagłówek", value=f"• {self.last_flash_audit.get('headline', 'Brak')} *({self.last_flash_audit.get('source', '')})*", inline=False)
            embed.add_field(name="⚡ Podjęta Akcja", value=self.last_flash_audit.get("action", "Brak"), inline=False)
            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            await self.compile_and_send_flash_news(ctx.channel, is_manual=True)

    @commands.command(name="crypto", aliases=["krypto"])
    async def crypto_news_shortcut(self, ctx: commands.Context) -> None:
        """Szybki skrót do najważniejszych newsów ze świata krypto."""
        await self.news_command(ctx, region="crypto")


async def setup(bot: commands.Bot) -> None:
    """Extension cog setup."""
    await bot.add_cog(NewsCog(bot))
