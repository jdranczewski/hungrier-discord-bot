import discord
from discord import app_commands

import asyncio
import datetime
import tempfile

from . import base_cog

class PurgeCog(base_cog.Cog):
    @app_commands.command(
        name="purge",
        description="Delete your messages in this channel older than a specified date."
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        year: int,
        month: int,
        day: int,
        delete: bool
    ):
        await interaction.response.send_message(
            f"Please confirm that you would like to **{'delete' if delete else 'archive'}** "
            f"your ({interaction.user.mention}) messages in "
            f"{interaction.channel.mention} from before {year}/{month}/{day}.",
            view=PurgeUI(datetime.datetime(year, month, day, 0, 0, 0), delete, timeout=None),
            ephemeral=True
        )

class PurgeUI(discord.ui.View):
    def __init__(self, before: datetime.datetime, delete: bool, *, timeout = 180):
        super().__init__(timeout=timeout)
        self._before = before
        self._delete = delete

    @discord.ui.button(label="Confirm the purge", style=discord.ButtonStyle.danger)
    async def button_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Purge confirmed. You will receive progress notifications via DM.",
            view=CancelUI(timeout=None)
        )
        purge_object = Purge(interaction.user, interaction.channel, self._before, self._delete)
        _purges.append(purge_object)
        await purge_object.run()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def button_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Purge cancelled. Have a good day!",
            view=None
        )

_purges = []
class Purge:
    def __init__(
            self,
            user: discord.User | discord.Member,
            channel: discord.TextChannel | discord.Thread,
            before: datetime.datetime,
            delete: bool
        ):
        self.user = user
        self.channel = channel
        self.before = before
        self.delete = delete
        self.stop_flag = False

    async def run(self):
        if not self.user.dm_channel:
            await self.user.create_dm()
        cancel_message = await self.user.dm_channel.send(
            f"{'Purge in' if self.delete else 'Archive of'} {self.channel.mention} initiated.\nYou have 30 seconds to cancel, "
            "and will be able to cancel at any point during the process too.",
            view=CancelUI(timeout=None)
        )
        await asyncio.sleep(30)

        try:
            # If the channel is archived, we need to unarchive it before deleting any messages
            unarchived = False
            if isinstance(self.channel, discord.Thread) and self.channel.archived:
                unarchived = True
                await self.channel.edit(archived=False)

            # Iterate over the messages, starting with the oldest
            deleted = 0
            output_file = tempfile.SpooledTemporaryFile(mode="w+b")
            status_message = await self.user.dm_channel.send("Getting messages...")
            message = None
            async for message in self.channel.history(
                limit=None, before=self.before, oldest_first=True
            ):
                if self.stop_flag:
                    break
                if message.author.id == self.user.id:
                    if self.delete:
                        await message.delete()
                        await asyncio.sleep(0.4)
                    output_file.write(
                        f"--- {message.created_at.strftime('%d/%m/%Y, %H:%M:%S')}: {message.content}\n".encode("utf-8")
                    )
                    deleted += 1
                    if deleted == 1 or deleted % 10 == 0:
                        await status_message.edit(
                            content=f"{'Deleted' if self.delete else 'Archived'} {deleted} messages "
                            f"in {self.channel.mention}.\n"
                            f"Reached {message.created_at.strftime('%d/%m/%Y, %H:%M:%S')} (starting from oldest).\n"
                            f"Stopping at {self.before.strftime('%d/%m/%Y, %H:%M:%S')}."
                        )
            if unarchived:
                await self.channel.edit(archived=True)
            await status_message.edit(
                content=f"# {'Purge' if self.delete else 'Archive'} {'cancelled' if self.stop_flag else 'completed'}.\n"
                f"{'Deleted' if self.delete else 'Archived'} {deleted} messages in {self.channel.mention}.\n" +
                (f"Reached {message.created_at.strftime('%d/%m/%Y, %H:%M:%S')} (starting from oldest).\n" if message else "") +
                f"Stop date at {self.before.strftime('%d/%m/%Y, %H:%M:%S')}.",
            )
            await cancel_message.delete()
        except Exception as e:
            await self.user.dm_channel.send(f"Exception occured: `{e}` - contact Jakub.")
            raise e
        finally:
            _purges.remove(self)
            output_file.seek(0)
            await self.user.dm_channel.send(
                file=discord.File(output_file, filename="archive.txt")
            )
            output_file.close()
    
    def stop(self):
        self.stop_flag = True

class CancelUI(discord.ui.View):
    @discord.ui.button(label="Cancel the purge", style=discord.ButtonStyle.danger)
    async def button_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Purge cancellation initiated. Check your DMs for confirmation.",
            view=None
        )
        for purge in _purges:
            if purge.user.id == interaction.user.id:
                purge.stop()

async def setup(bot):
    await bot.add_cog(PurgeCog(bot))