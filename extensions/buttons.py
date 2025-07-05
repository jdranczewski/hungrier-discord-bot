import discord
import discord.ui
from discord import app_commands
from discord.ext import commands

class UI(discord.ui.View):
    @discord.ui.button(label="Button 1")
    async def button_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Button 1 pressed.")

    @discord.ui.button(emoji="😔", style=discord.ButtonStyle.blurple)
    async def button_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Sad times")

class Buttons(commands.Cog):
    @app_commands.command(name="buttons", description="Show some buttons")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=UI(timeout=None))

async def setup(bot):
    await bot.add_cog(Buttons(bot))