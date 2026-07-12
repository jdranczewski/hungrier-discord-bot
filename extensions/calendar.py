import calendar
from tracemalloc import start
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from . import base_cog
from extensions import _date_parser

import uuid
import icalendar
import datetime

class EnableDisableCalendar(base_cog.Cog):
    db_structure = """
CREATE TABLE IF NOT EXISTS "forum_channels" (
	"id"	  INTEGER NOT NULL UNIQUE,
	"guild"	  INTEGER NOT NULL,
	"forum"	  INTEGER NOT NULL,
    "hash"    TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
"""
    @app_commands.command(
        name="enable_calendar",
        description="Enable calendar generation for a forum channel."
    )
    async def enable(
        self,
        interaction: discord.Interaction,
        channel: discord.ForumChannel
    ):
        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message(
                f"Calendars can only be enabled for forum channels in **this** server.",
                ephemeral=True
            )
            return
        # Check if a row matching all three already exists
        cursor = self.bot.dbconn.execute(
            "SELECT id FROM forum_channels WHERE guild=? AND forum=?",
            (interaction.guild_id, channel.id)
        )
        if cursor.fetchone():
            await interaction.response.send_message(
                f"Calendar already enabled for {channel.mention}.",
                ephemeral=True
            )
        else:
            hash = str(uuid.uuid1())
            self.bot.dbconn.execute(
                "INSERT INTO forum_channels (guild, forum, hash) VALUES (?, ?, ?)",
                (interaction.guild_id, channel.id, hash)
            )
            self.bot.dbconn.commit()
            await interaction.response.send_message(f"Calendar enabled for {channel.mention}.")
    
    @app_commands.command(
        name="disable_calendar",
        description="Disable calendar generation for a forum channel."
    )
    async def disable(
        self,
        interaction: discord.Interaction,
        channel: discord.ForumChannel
    ):
        cursor = self.bot.dbconn.execute(
            "DELETE FROM forum_channels WHERE guild=? AND forum=?",
            (interaction.guild_id, channel.id)
        )
        # Confirm with the user if the deletion was succesful
        if cursor.rowcount:
            await interaction.response.send_message(f"Calendar disabled for {channel.mention}.")
        else:
            await interaction.response.send_message(f"No calendar enabled for {channel.mention}.", ephemeral=True)


class CalendarParse(base_cog.Cog):
    @app_commands.command(
        name="sync_calendar",
        description="Sync calendars in this server."
    )
    async def sync_command(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                f"This command only works in servers.",
                ephemeral=True
            )
            return
        await interaction.response.send_message("Scanning...", ephemeral=True)
        await self.parse_calendars(interaction.guild.id)
        await interaction.edit_original_response(
            content="Calendar updates done!"
        )

    async def parse_calendars(self, guild_id: None | int = None):
        if guild_id is not None:
            cursor = self.bot.dbconn.execute(
                "SELECT * FROM forum_channels WHERE guild=?",
                (guild_id,)
            )
        else:
            cursor = self.bot.dbconn.execute(
                "SELECT * FROM forum_channels",
            )
        for row in cursor:
            forum = await self.bot.fetch_channel(row["forum"])
            if not isinstance(forum, discord.ForumChannel):
                raise Exception("Not a ForumChannel")
            guild = await self.bot.fetch_guild(row["guild"])
            calendar = icalendar.Calendar.new(name=guild.name)
            threads = list(forum.threads)
            async for thread in forum.archived_threads():
                print("archived", thread)
                threads.append(thread)
            for thread in threads:
                past_reference = thread.created_at
                if past_reference is None:
                    start_message = await thread.fetch_message(thread.id)
                    past_reference = start_message.created_at
                for date in _date_parser.parse_dates(thread.name, past_reference.date()):
                    event = icalendar.Event.new(
                        summary=thread.name,
                        start=date.date,
                        end=date.date,
                        links=thread.jump_url,
                        uid=str(thread.id)
                    )
                    calendar.add_component(event)
            with open(f"/var/www/hosting/hungrier/{row['hash']}.ics", "w") as f:
                f.write(calendar.to_ical().decode("utf-8"))


async def setup(bot):
    await bot.add_cog(EnableDisableCalendar(bot))
    await bot.add_cog(CalendarParse(bot))