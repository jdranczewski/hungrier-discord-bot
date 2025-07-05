import discord
from discord.ext import commands
from discord import app_commands

class Ping(commands.Cog):
    @app_commands.command(name="ping", description="Are you still there?")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

async def setup(bot):
    await bot.add_cog(Ping(bot))