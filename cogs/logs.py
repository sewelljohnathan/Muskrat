import discord

from discord.ext import commands
from utils.database import get_guild_data, log_to_database, update_database_guild
from utils.message import send_message


class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'add': self.add,
            'show': self.show,
            'reset': self.reset,
            'help': self.help
        }

    @commands.command()
    async def logs(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'show'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @staticmethod
    async def add(ctx, args):
        """Logs text to the database."""
        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        log_to_database(ctx.guild, f'[User Generated] {args}')

    @staticmethod
    async def show(ctx, args):
        """Show guild logs."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get guild data
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Check if the user wants to limit the number of logs
        limit = None
        if args:
            try:
                limit = int(args)
            except ValueError:
                await send_message(ctx.channel, f'Could not parse limit "{args}".')
                return

        # Get the logs list
        guild_data['logs'].reverse()
        if limit:
            logs = guild_data['logs'][:limit]
        else:
            logs = guild_data['logs']
        logs.reverse()

        # Create log output
        output = '```Server Logs'
        if limit:
            output += f' (last {limit})'
        else:
            output += f' (full history)'
        output += '\n\n'

        for log in logs:
            output += f'{log}\n'
        output += '```'
            
        # Send logs
        await send_message(ctx.channel, output)

    @staticmethod
    async def reset(ctx, args):
        """Resets guild logs."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        updated = update_database_guild(
            guild,
            {"$set": {"logs": []}},
            'Failed to reset guild logs.'
        )
        if updated:
            await send_message(ctx.channel, 'Server logs have successfully been reset.') 

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Logs Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages logs for the server.

        Logs are primarily used for the bot to record potential errors for troublshooting issues,
        but they can also be used to store your own data.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}logs help`
        Show this message.
        Required Permission: Everyone

        `{prefix}logs add [text]`
        Logs [text].
        Required Permission: Manage Messages

        `{prefix}logs show [limit]`
        Shows the past [limit] logs. Omit [limit] to show all logs.
        Required Permission: Manage Messages

        `{prefix}logs reset`
        Deletes all logs for this server. There is no way to recover them.
        Required Permission: Administrator
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)
        
        # Send embed
        await send_message(channel=ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Logs(bot))