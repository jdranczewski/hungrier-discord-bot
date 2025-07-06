import discord
from discord.ext import commands, autoreload
from discord import app_commands
import sqlite3

import config

class Hungrier(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("extensions.ping")
        await self.load_extension("extensions.buttons")
        self._reloader = autoreload.Reloader(ext_directory="extensions")
        self._reloader.start(self)

        # Sync command tree to the testing guild
        # if config.testing_guild:
        #     guild = discord.Object(config.testing_guild)
        #     self.tree.copy_global_to(guild=guild)
        #     await self.tree.sync(guild=guild)


def main():
    # Establish intents
    intents = discord.Intents.default()
    # intents.message_content = True

    # Create the bot
    bot = Hungrier(
        command_prefix=commands.when_mentioned,
        intents=intents
    )

    # Sync command tree on demand
    @bot.command(name="sync")
    async def sync(ctx: commands.Context):
        synced = await bot.tree.sync()
        await ctx.send(
            f"Synced {len(synced)} commands."
        )

    # Run the bot
    with sqlite3.connect("main.db") as dbconn:
        dbconn.row_factory = sqlite3.Row
        bot.dbconn = dbconn
        bot.run(config.token)

if __name__ == "__main__":
    main()
