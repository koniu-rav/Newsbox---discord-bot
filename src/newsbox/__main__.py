"""Entry point to launch the Newsbox Discord Bot."""

import asyncio
import sys
from newsbox.bot import NewsboxBot
from newsbox.config import get_settings
from newsbox.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """Main startup routine."""
    settings = get_settings()

    if not settings.discord_bot_token:
        logger.error(
            "DISCORD_BOT_TOKEN is not set. Please provide it in your environment or .env file."
        )
        sys.exit(1)

    bot = NewsboxBot()

    try:
        bot.run(settings.discord_bot_token)
    except KeyboardInterrupt:
        logger.info("Newsbox bot stopped by user.")
    except Exception as e:
        logger.critical("Fatal error running bot: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

