import discord
from discord import app_commands

import asyncio
import datetime
import tempfile
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
        default=str(24),
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        text = self.options.value
        polls = text.split("\n\n")
        assert isinstance(self.multiple.component, discord.ui.Checkbox)
        multiple = self.multiple.component.value
        duration = datetime.timedelta(hours=int(self.duration.value))

        # Initial response
        with tempfile.SpooledTemporaryFile(
            mode="w+b"
        ) as file:
            file.write(text.encode("utf-8"))
            file.seek(0)
            await interaction.response.send_message(
                f'Thanks! Sending polls now...',
                file=discord.File(file, filename="polls.txt"),  # ty:ignore[invalid-argument-type]
                ephemeral=True
            )

        if interaction.channel is None or isinstance(interaction.channel, (discord.ForumChannel, discord.CategoryChannel)):
            raise Exception("Channel type not supported")
        await interaction.channel.send(
            content=f"Poll{'s' if len(polls)>1 else ''} from {interaction.user.mention}:"
        )
        emoji_names = None
        for i, poll in enumerate(polls):
            options = [option for option in poll.split("\n") if len(option)]
            discord_poll = discord.Poll(
                f"(vote {i+1}) {options[0].split(';')[0]} vs {options[1].split(';')[0]}" if len(options)==2 else f"Vote number {i+1}",
                duration,
                multiple=multiple
            )
            for option in options:
                if ";" in option:
                    text, emoji = option.split(";")
                    emoji = emoji.replace(" ", "")
                    if len(emoji)>2 and emoji[0] == ":" and emoji[-1] == ":":
                        # try to find the emoji name on the current server
                        emoji = emoji[1:-1]
                        if emoji_names is None:
                            emoji_names = {}
                            if interaction.guild is not None:
                                emoji_names = {emoji.name: emoji for emoji in interaction.guild.emojis}
                        if emoji in emoji_names:
                            emoji = emoji_names[emoji]
                        else:
                            emoji = None
                    discord_poll.add_answer(
                        text=text,
                        emoji=emoji
                    )
                else:
                    discord_poll.add_answer(
                        text=option,
                    )
            if len(options):
                await interaction.channel.send(poll=discord_poll)
                await asyncio.sleep(3)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if not interaction.response.is_done:
            await interaction.response.send_message(
                f'Oops! Something went wrong. (`{error}`)',
                ephemeral=True
            )
        else:
            await interaction.edit_original_response(
                content=f'Oops! Something went wrong. (`{error}`)'
            )

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

async def setup(bot):
    await bot.add_cog(PollsCog(bot))