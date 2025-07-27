from discord.ext import commands

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .. import main

class Cog(commands.Cog):
    def __init__(self, bot: "main.Hungrier"):
        self.bot = bot

    db_structure = None
    async def cog_load(self):
        if self.db_structure:
            self.bot.dbconn.execute(self.db_structure)