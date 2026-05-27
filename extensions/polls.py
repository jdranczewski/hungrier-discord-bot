import discord
from discord import app_commands

import datetime
import traceback

from . import base_cog

class PollsCog(base_cog.Cog):
    @app_commands.command(
        name="polls",
        description="Run multiple polls based on a list of options."
    )
    async def purge(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.send_modal(PollsModal())

class PollsModal(discord.ui.Modal, title='Polls'):
    options = discord.ui.TextInput(
        label='Options:',
        style=discord.TextStyle.long,
        placeholder='Paste your poll options here...',
        required=True,
    )

    description = discord.ui.TextDisplay(
        content="-# Each option should be on its own line. "
        "Separate polls should be separated with an empty line. "
        "Emoji can be included after a semicolon, the easiest way to get "
        "the emoji formatting right is to send the draft as a Discord message and "
        "select 'Copy Text' from the Discord UI."
    )

    multiple = discord.ui.Label(
        text="Multiple choice?",
        component=discord.ui.Checkbox()
    )

    duration = discord.ui.TextInput(
        label="Duration (hours):",
        default=24,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        text = self.options.value
        polls = text.split("\n\n")
        multiple = self.multiple.component.value
        duration = datetime.timedelta(hours=int(self.duration.value))
        await interaction.response.send_message(f'Thanks! Sending polls now...', ephemeral=True)
        await interaction.channel.send(
            content=f"Polls from {interaction.user.mention}:"
        )
        for i, poll in enumerate(polls):
            discord_poll = discord.Poll(
                f"Vote number {i+1}", duration,
                multiple=multiple
            )
            for option in poll.split("\n"):
                if ";" in option:
                    text, emoji = option.split(";")
                    emoji = emoji.replace(" ", "")
                    discord_poll.add_answer(
                        text=text,
                        emoji=emoji
                    )
                else:
                    discord_poll.add_answer(
                        text=option,
                    )
            await interaction.channel.send(poll=discord_poll)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if not interaction.response.is_done:
            await interaction.response.send_message(
                f'Oops! Something went wrong. (`{error}`)',
                ephemeral=True
            )
        else:
            await interaction.channel.send(f'Oops! Something went wrong. (`{error}`)')

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

async def setup(bot):
    await bot.add_cog(PollsCog(bot))