import discord
from discord import app_commands

import tempfile

from . import base_cog

class CountThreads(base_cog.Cog):
    @app_commands.command(name="count_threads", description="How many threads are there in the server?")
    async def ping(self, interaction: discord.Interaction):
        response = await interaction.response.send_message("Scanning...")
        total_threads = 0
        total_channels = len(interaction.guild.channels)
        output_file = tempfile.SpooledTemporaryFile(mode="w+b")
        def print_file(text):
            output_file.write((text + "\n").encode("utf-8"))
        for i, channel in enumerate(interaction.guild.channels):
            channel_threads = 0
            print_file(f"#{channel}")
            try:
                if hasattr(channel, "threads"):
                    for thread in channel.threads:
                        print_file(f"   {thread}")
                        channel_threads += 1
                if hasattr(channel, "archived_threads"):
                    async for thread in channel.archived_threads():
                        print_file(f"   (archived) {thread}")
                        channel_threads += 1
            except Exception as e:
                print_file(f"   {e}")
            if channel_threads:
                print_file(f"{channel_threads} thread{'s' if channel_threads != 1 else ''}")
                total_threads += channel_threads
            print_file("")
            
            await response.resource.edit(
                content=f"Scanning... ({i+1}/{total_channels} channels done, "
                f"{total_threads} thread{'s' if total_threads != 1 else ''} so far)"
            )
        print_file(
            f"--- {total_threads} thread{'s' if total_threads != 1 else ''} total, "
            f"{total_channels} channel{'s' if total_channels != 1 else ''} --- "
            )
        output_file.seek(0)
        await response.resource.edit(
            content=f"There are {total_threads} threads ({total_channels} channel{'s' if total_channels != 1 else ''}) in this server.",
            attachments=[discord.File(output_file, filename="archive.txt")]
        )
        output_file.close()

async def setup(bot):
    await bot.add_cog(CountThreads(bot))