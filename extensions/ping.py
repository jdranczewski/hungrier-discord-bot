import discord
from discord import app_commands

from . import base_cog

class Ping(base_cog.Cog):
    @app_commands.command(name="ping", description="Are you still there?")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

async def setup(bot):
    await bot.add_cog(Ping(bot))