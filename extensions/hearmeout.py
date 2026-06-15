import discord
from discord import app_commands

import datetime
import re
import traceback

from . import base_cog

class HearMeOutCog(base_cog.Cog):
    @app_commands.command(
        name="hearmeout",
        description="Anonymously proxy a hear-me-out message and poll."
    )
    async def hearmeout(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.send_modal(HearMeOutModal())


emoji_re = re.compile(r":([a-zA-Z0-9~_]+):")

class HearMeOutModal(discord.ui.Modal, title='Hear me out?'):
    name = discord.ui.TextInput(
        label="Character name:",
        required=True
    )

    description = discord.ui.TextInput(
        label='Description / shilling:',
        style=discord.TextStyle.long,
        placeholder='Why are they hot?',
        required=True,
    )

    # description = discord.ui.TextDisplay(
    #     content="-# Note that if you want to use custom emoji, they're going to "
    # )

    files  = discord.ui.Label(
        text="Upload images:",
        component=discord.ui.FileUpload(
            required=False,
            max_values=3
        )
    )

    duration = discord.ui.TextInput(
        label="Poll duration (hours):",
        default=str(72),
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Posting hear me out message and poll...",
            ephemeral=True
        )
        content = f"# {self.name.value}"

        # Parse description and insert server emoji
        description = self.description.value
        server_emoji = {}
        if interaction.guild is not None:
            server_emoji = {emoji.name: emoji for emoji in interaction.guild.emojis}
        offset = 0
        for match in emoji_re.finditer(description):
            span = [x+offset for x in match.span()]
            if span[0]-1 >= 0 and description[span[0]-1] == "<":
                continue
            emoji_name = match.group(1)
            if emoji_name in server_emoji:
                emoji = server_emoji[emoji_name]
                replacement = f"<:{emoji.name}:{emoji.id}>"
                description = description[:span[0]] + replacement + description[span[1]:]
                offset += len(replacement) - len(emoji_name) - 2
        
        assert isinstance(self.files.component, discord.ui.FileUpload)
        files = self.files.component.values
        files = [await x.to_file() for x in files][::-1]

        duration = datetime.timedelta(hours=int(self.duration.value))
        discord_poll = discord.Poll(
            f"Is {self.name.value} a Hear Me Out?", duration,
        )
        for answer, emoji in zip(
            (
                "Yes (weird and not hot)",
                "Yes but I get it (weird but hot)",
                "No (conventionally attractive)",
                "No but im judging you (hot but ew)"
            ),
            (
                "<:sickosYES:1305559994455953458>",
                "<:HMMMMM:844332400095002644>",
                "<:sickosno:1310345844884504677>",
                "<:confusion:851499609959563274>",
            )
        ):
            discord_poll.add_answer(
                text=answer,
                emoji=emoji
            )

        if interaction.channel is None or isinstance(interaction.channel, (discord.ForumChannel, discord.CategoryChannel)):
            raise Exception("Channel type not supported")
        await interaction.channel.send(
            content=content,
            files=files,
        )
        await interaction.channel.send(
            content=f"-# Hear me out:\n{description}",
        )
        await interaction.channel.send(
            poll=discord_poll
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if not interaction.response.is_done:
            await interaction.response.send_message(
                f'Oops! Something went wrong. (`{error}`)',
                ephemeral=True
            )
        else:
            await interaction.edit_original_response(
                content=f'Oops! Something went wrong. (`{error}`)',
            )

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

async def setup(bot):
    await bot.add_cog(HearMeOutCog(bot))