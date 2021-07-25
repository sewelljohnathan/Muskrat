import discord

from discord.ext import commands
from utils.database import get_guild_data, update_database_guild
from utils.message import delete_message, send_message


class BannedWords(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'add': self.add,
            'remove': self.remove,
            'list': self.list,
            'reset': self.reset,
            'help': self.help             
        }

    @commands.command(aliases=['bw'])
    async def banned_words(self, ctx, command=None, *, args=None):
        """Manages subcommands."""
        command = command or 'help'
        if command in self.subcommands:
            await self.subcommands[command](ctx, args)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Deletes a message if it contains a banned word."""
        guild = message.guild
        # This allows the bot to list the banned words, or mods to use them in commands
        if message.author.guild_permissions.manage_messages:
            return

        # Get the guild data from the database
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Delete the message if it contains a banned word
        for word in guild_data['banned_words']:
            if word.lower() in message.content.lower():
                await delete_message(message)
                return

    @staticmethod
    async def add(ctx, args):
        """Adds a banned word to the database."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Return if no argument is provided
        if not args:
            return
        word = args

        # Add the word to the database
        updated = update_database_guild(
            guild,
            {"$push": {"banned_words": word}},
            'Failed to remove a banned word.'
        )
        if updated:
            await send_message(ctx.channel, f'"{word}" is now a banned word.')

    @staticmethod
    async def remove(ctx, args):
        """Removes a banned word from the database."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Return if no argument is provided
        if not args:
            return
        word = args

        # Remove the word to the database
        updated = update_database_guild(
            guild,
            {"$pull": {"banned_words": word}},
            'Failed to remove a banned word.'
        )
        if updated:
            await send_message(ctx.channel, f'"{word}" is no longer a banned word.')

    @staticmethod
    async def list(ctx, args):
        """Sends a list of banned words."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get the guild data from the database
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Get the list of banned words
        banned_words = sorted(guild_data['banned_words'])
        words = ''
        for word in banned_words:
            words += word + '\n'
        if not banned_words:
            words += 'Your server has no banned words.\n'

        # Create embed
        embed = discord.Embed(title='Banned Words', color=ctx.bot.embed_color)
        embed.add_field(name='***Words***', value=words, inline=True)

        # Send embed
        await send_message(ctx.channel, embed=embed)

    @staticmethod
    async def reset(ctx, args):
        """Resets the list of banned words."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Update database
        updated = update_database_guild(
            guild,
            {"$set": {"banned_words": []}},
            'Failed to reset banned words.'
        )
        if updated:
            await send_message(ctx.channel, 'Banned words have successfully been reset.')

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Banned Words Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages banned words throughout the server.

        If a message containing any banned words is sent by a member without the Manage Messages permission, it will be deleted.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}bw help`
        Show this message.
        Required Permission: Everyone

        `{prefix}bw add [word]`
        Adds [word] to the server's list of banned words.
        Required Permission: Manage Messages

        `{prefix}bw remove [word]`
        Removes [word] from the server's list of banned words.
        Required Permission: Manage Messages

        `{prefix}bw list`
        Displays a list of all banned words.
        Required Permission: Manage Messages

        `{prefix}bw reset`
        Resets the list of banned words.
        Required Permission: Manage Messages
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(BannedWords(bot))
