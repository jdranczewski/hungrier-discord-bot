import discord
from discord import app_commands
from discord.ext import commands

from . import base_cog

class EnableDisable(base_cog.Cog):
    db_structure = """
CREATE TABLE IF NOT EXISTS "voice_channels" (
	"id"	  INTEGER NOT NULL UNIQUE,
	"guild"	  INTEGER NOT NULL,
	"voice"	  INTEGER NOT NULL,
	"text"	  INTEGER NOT NULL,
    "message" INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
"""
    @app_commands.command(
        name="enable_vn",
        description="Enable notifications for a voice channel."
    )
    async def enable(
        self,
        interaction: discord.Interaction,
        channel: discord.VoiceChannel
    ):
        # Check if a row matching all three already exists
        cursor = self.bot.dbconn.execute(
            "SELECT id FROM voice_channels WHERE guild=? AND voice=? AND text=?",
            (interaction.guild_id, channel.id, interaction.channel_id)
        )
        if cursor.fetchone():
            await interaction.response.send_message(
                f"Notifications already enabled for {channel.mention}.",
                ephemeral=True
            )
        else:
            self.bot.dbconn.execute(
                "INSERT INTO voice_channels (guild, voice, text) VALUES (?, ?, ?)",
                (interaction.guild_id, channel.id, interaction.channel_id)
            )
            self.bot.dbconn.commit()
            await interaction.response.send_message(f"Notifications enabled for {channel.mention}.")
    
    @app_commands.command(
        name="disable_vn",
        description="Disable notifications for a voice channel."
    )
    async def disable(
        self,
        interaction: discord.Interaction,
        channel: discord.VoiceChannel
    ):
        cursor = self.bot.dbconn.execute(
            "DELETE FROM voice_channels WHERE guild=? AND voice=? AND text=?",
            (interaction.guild_id, channel.id, interaction.channel_id)
        )
        # Confirm with the user if the deletion was succesful
        if cursor.rowcount:
            await interaction.response.send_message(f"Notifications disabled for {channel.mention}.")
        else:
            await interaction.response.send_message(f"No notifications enabled for {channel.mention}.", ephemeral=True)


class Notify(base_cog.Cog):
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        # Handle VC join events (not in VC before, in a VC after)
        if before.channel is None and after.channel is not None:
            channel = after.channel
            # Get all the text channels that we should send notifications to
            cursor = self.bot.dbconn.execute(
                "SELECT * FROM voice_channels WHERE guild=? AND voice=?",
                (channel.guild.id, channel.id)
            )
            for row in cursor:
                # Fetch the text channel based on its ID and send a message
                text_channel = await self.bot.fetch_channel(row["text"])
                await text_channel.send(f"{member.display_name} joined {channel.mention}!")


async def setup(bot):
    await bot.add_cog(EnableDisable(bot))
    await bot.add_cog(Notify(bot))