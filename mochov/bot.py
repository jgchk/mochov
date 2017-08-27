import logging
import sys
import traceback

from discord.ext import commands

from mochov.config.config import Config

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

extensions = ["cogs.mochov"]


class Bot(commands.Bot):
    async def on_ready(self):
        loaded_extensions, failed_extensions = await self.load_extensions()
        logger.info("LOADED: {}".format(loaded_extensions))
        logger.info("FAILED: {}".format(failed_extensions))

    async def load_extensions(self):
        loaded_extensions = []
        failed_extensions = []

        for extension in extensions:
            try:
                self.load_extension(extension)
            except ImportError:
                failed_extensions.append((extension, traceback.format_exc()))
            else:
                loaded_extensions.append(extension)

        return loaded_extensions, failed_extensions


if __name__ == '__main__':
    config = Config()
    if not config.discord_prefix:
        print("Please set a command prefix in config.ini")
        sys.exit()
    if not config.discord_token:
        print("Please enter your Discord bot account token in config.ini")
        sys.exit()

    bot = Bot(command_prefix=config.discord_prefix)
    bot.run(config.discord_token)
