from discord.ext import commands

class Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    db_structure = None
    async def cog_load(self):
        if self.db_structure:
            self.bot.dbconn.execute(self.db_structure)