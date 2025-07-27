import asyncio
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
    "overview_message" INTEGER,
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
    db_structure = """
CREATE TABLE IF NOT EXISTS "voice_members" (
	"id"	INTEGER NOT NULL UNIQUE,
	"member"	INTEGER NOT NULL,
	"channel"	INTEGER NOT NULL,
	"message"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("channel") REFERENCES "voice_channels"("id")
);
"""

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        # Handle VC join events (not in VC before, in a VC after)
        # Joins are only handled if we catch them live (no point sending a 
        # notification otherwise), but leaves should probably be made consistent
        # every time we get an event here, to avoid a situation where there are
        # entries in the database for people who have since left.
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
                len_others = len(channel.members) - 1
                others = "" if len_others < 1 else f" with {len(channel.members)-1} other"
                if len_others > 2:
                    others += "s"
                message = await text_channel.send(f"{member.display_name} joined {channel.mention}{others}!")
                self.bot.dbconn.execute(
                    "INSERT INTO voice_members (member, channel, message) VALUES (?, ?, ?)",
                    (member.id, row["id"], message.id)
                )
                self.bot.dbconn.commit()
                await asyncio.sleep(5)
                try:
                    await message.edit(content=f"{member.display_name} joined {channel.mention}!")
                except discord.errors.NotFound:
                    # The message was deleted
                    pass

        elif before.channel is not None and after.channel is None:
            channel = before.channel
            cursor = self.bot.dbconn.execute(
                "SELECT voice_members.id, voice_channels.text, voice_members.message FROM voice_members "
                "LEFT JOIN voice_channels on voice_members.channel=voice_channels.id "
                "WHERE member=? AND voice=?",
                (member.id, channel.id)
            )
            for row in cursor:
                self.bot.dbconn.execute(
                    "DELETE FROM voice_members WHERE id=?",
                    (row["id"],)
                )
                self.bot.dbconn.commit()
                if row["message"]:
                    text_channel = await self.bot.fetch_channel(row["text"])
                    message = await text_channel.fetch_message(row["message"])
                    await message.delete()

async def setup(bot):
    await bot.add_cog(EnableDisable(bot))
    await bot.add_cog(Notify(bot))