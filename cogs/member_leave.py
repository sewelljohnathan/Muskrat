import discord

from discord.ext import commands
from utils.channel import convert_to_channel
from utils.database import get_guild_data, update_database_guild
from utils.message import send_message


class MemberLeave(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'channel': self.channel,
            'help': self.help
        }

    @commands.command(aliases=['leave'])
    async def member_leave(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'help'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Sends a message when a member leaves the guild."""
        guild = member.guild

        # Get guild data
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Send leave message
        leave_channel = discord.utils.get(guild.text_channels, id=guild_data['leave_channel_id'])
        await send_message(leave_channel, f'{member.mention} has left the server.')

    @staticmethod
    async def channel(ctx, args):
        """Sets the leave channel."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return
        
        # Get guild data
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Get the leave channel
        leave_channel = await convert_to_channel(ctx, args)
        if leave_channel is None:
            await send_message(ctx.channel, f'Failed to parse "{args}" as a channel.')
            return

        # update the database
        updated = update_database_guild(
            guild, 
            {"$set": {"leave_channel_id": leave_channel.id}},
            'Failed to change leave channel.'
        )
        if updated == False:
            return

        await send_message(ctx.channel, f'Leave Channel successfully changed to {args}.')

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Member Leave Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages members leaving the server.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}leave help`
        Show this message.
        Required Permission: Everyone

        `{prefix}leave channel [text channel]`
        Sets [text channel] for leave messages to be sent.
        Required Permission: Administrator
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(MemberLeave(bot))