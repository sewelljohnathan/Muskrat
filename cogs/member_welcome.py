import discord

from discord.ext import commands
from utils.channel import convert_to_channel
from utils.database import get_guild_data, update_database_guild
from utils.message import send_message
from utils.role import convert_to_role, give_member_role


class MemberWelcome(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.subcommands = {
            'channel': self.channel,
            'role': self.role,
            'message': self.message,
            'help': self.help
        }

    @commands.command(aliases=['welcome'])
    async def member_welcome(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'help'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Sends a message when a member joins the guild."""
        guild = member.guild

        # Get guild data
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Get welcome channel
        welcome_channel = discord.utils.get(guild.channels, id=guild_data['welcome_channel_id'])
        if welcome_channel:

            # Send welcome message
            welcome_message = f'Welcome {member.mention} to **{guild.name}**! {guild_data["welcome_message"]}'
            await send_message(welcome_channel, welcome_message)

        # Give welcome role
        welcome_role = discord.utils.get(guild.roles, id=guild_data['welcome_role_id'])
        if welcome_role:
            await give_member_role(member, welcome_role)

    @staticmethod
    async def channel(ctx, args):
        """Sets the welcome channel."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get welcome channel
        welcome_channel = await convert_to_channel(ctx, args)
        if welcome_channel is None:
            await send_message(ctx.channel, f'Failed to parse "{args}" as a channel.')
            return

        # Update database
        updated = update_database_guild(
            guild, 
            {"$set": {"welcome_channel": welcome_channel}},
            'Failed to change welcome channel.'
        )
        if updated:
            await send_message(ctx.channel, f'Welcome Channel successfully changed to {welcome_channel.mention}')

    @staticmethod
    async def role(ctx, args):
        """Sets the welcome role."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get welcome role
        welcome_role = await convert_to_role(ctx, args)
        if welcome_role is None:
            await send_message(ctx.channel, f'Failed to parse "{args}" as a role.')
            return

        # Update database
        updated = update_database_guild(
            guild, 
            {"$set": {"welcome_role": welcome_role}},
            'Failed to change welcome role.'
        )
        if updated:
            await send_message(ctx.channel, f'Custom welcome message set to "{args}"')

    @staticmethod
    async def message(ctx, args):
        """Sets the welcome message."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get welcome message
        welcome_message = args if args else ''

        # Update database
        updated = update_database_guild(
            guild, 
            {"$set": {"welcome_message": welcome_message}},
            'Failed to change welcome message.'
        )
        if updated:
            await send_message(ctx.channel, f'Custom welcome message set to "{args}"')

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Member Join Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages members joining the server.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}welcome help`
        Show this message.
        Required Permission: Everyone

        `{prefix}welcome message [text]`
        Sets [text] as the custom welcome message for members joining the server.
        Required Permission: Administrator

        ``{prefix}welcome role [role]`
        Sets [role] as the role to be given automatically to new members.
        Required Permission: Administrator

        `{prefix}welcome channel [text channel]`
        Sets [text channel] for welcome messages to be sent.
        Required Permission: Administrator
        '''   
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(client):
    client.add_cog(MemberWelcome(client))