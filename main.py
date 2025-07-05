import discord
from discord.ext import commands, autoreload
from discord import app_commands

import config

class Hungrier(commands.Bot):
    pass


def main():
    # Establish intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Create the bot
    bot = Hungrier(command_prefix="!hg ", intents=intents)
    reloader = autoreload.Reloader(ext_directory="extensions")

    # Set up extensions when bot is ready
    @bot.event
    async def on_ready():
        await bot.load_extension("extensions.ping")
        reloader.start(bot)

    # Run the bot
    bot.run(config.token)

if __name__ == "__main__":
    main()
