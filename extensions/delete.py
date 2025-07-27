import discord
from discord.ext import commands

from . import base_cog

class Delete(base_cog.Cog):
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if (
            payload.message_author_id == self.bot.user.id
            and payload.event_type == "REACTION_ADD"
            and payload.emoji.name == "❌"
        ):
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.delete()


async def setup(bot):
    await bot.add_cog(Delete(bot))