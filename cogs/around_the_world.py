import discord

from discord.ext import commands
from utils.message import delete_message, get_message, send_message


class AroundTheWorld(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'help': self.help,
        }

    @commands.command(aliases=['atw'])
    async def around_the_world(self, ctx, command=None, *, args=None):
        """Manages subcommands."""
        command = command or 'help'
        if command in self.subcommands:
            await self.subcommands[command](ctx, args)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """Prevent editing."""
        channel = self.bot.get_channel(payload.channel_id)
        if channel.name != 'around-the-world':
            return

        message = await get_message(channel, payload.message_id)
        await delete_message(message)

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Around The World', color=ctx.bot.embed_color)

        description = '''
        This Cog manages a channel with the name [#around-the-world].

        All messages sent with content other than 'around the world' are automatically deleted.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)
        
        prefix = ctx.prefix
        command_list = f'''
        `{prefix}atw help`
        Show this message.
        Required Permission: Everyone
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)
        
        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(AroundTheWorld(bot))
