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

    # Sync command tree on demand
    @bot.command(name="sync")
    async def sync(ctx: commands.Context):
        synced = await bot.tree.sync()
        await ctx.send(
            f"Synced {len(synced)} commands."
        )

    # Set up extensions when bot is ready
    @bot.event
    async def on_ready():
        await bot.load_extension("extensions.ping")
        await bot.load_extension("extensions.buttons")
        reloader.start(bot)

    # Run the bot
    bot.run(config.token)

if __name__ == "__main__":
    main()
