import discord
from discord import app_commands

import math

from . import base_cog

class EmojiRoundup(base_cog.Cog):
    @app_commands.command(name="emoji_roundup", description="Display all server emoji as reactions")
    async def emoji_roundup(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command only works in servers.")
            return
        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message("This command only works in text channels.")
            return
        emojis = [emoji for emoji in guild.emojis if not emoji.animated]
        N = len(emojis)
        await interaction.response.send_message(f"Here are the **{N}** emoji from this server:")
        N_messages = math.ceil(N/20)
        for i in range(N_messages):
            message: discord.Message = await channel.send(content=f"set {i+1}/{N_messages}")
            for emoji in emojis[i*20:(i+1)*20]:
                await message.add_reaction(emoji)

async def setup(bot):
    await bot.add_cog(EmojiRoundup(bot))