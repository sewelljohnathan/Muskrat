import os
import discord

from dotenv import load_dotenv
from discord.ext import commands
from utils.database import add_database_member, add_database_guild, log_to_database
from utils.message import send_message


def main():

    # Create the bot
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix='!!', intents=intents, help_command=None)
    bot.embed_color = 0x00C700

    # Help Command
    @bot.command()
    async def help(ctx):
        """Help Command"""
        # Create embed
        embed = discord.Embed(title='**Muskrat Bot Commands**', color=ctx.bot.embed_color)
        prefix = ctx.bot.command_prefix

        command_list = f'''
        **Around The World**
        `{prefix}around_the_world`
        `{prefix}atw`
        **Banned Words**
        `{prefix}banned_words`
        `{prefix}bw`
        **Counting**
        `{prefix}counting`
        **Member Leave**
        `{prefix}member_leave`
        `{prefix}leave`
        **Member Welcome**
        `{prefix}member_welcome`
        `{prefix}welcome`
        **Private VC's**
        `{prefix}private_vc`
        `{prefix}pvc`
        **Reaction Roles**
        `{prefix}reaction_role`
        `{prefix}rr`
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=True)

        additional_info = f'''
        - Use `{prefix}[command] help` to get information on how to use specific commands.
        '''
        embed.add_field(name='***Additional Information***', value=additional_info, inline=False)

        support = f'''
        For additional support or questions, join Muskrat's home here:
        https://discord.gg/afbjcYFKvr
        To invite Muskrat to your own server, use this link:
        {discord.utils.oauth_url(client_id=bot.user.id, permissions=discord.Permissions(permissions=8))}        
        '''
        embed.add_field(name='***Support***', value=support, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)

    # Common events
    @bot.event
    async def on_ready():
        """Confirms bot is online."""
        print('Muskrat is online.')
        await bot.change_presence(activity=discord.Game(name='Watching over my territory.'))

    @bot.event
    async def on_guild_join(guild):
        """Adds a guild to the database."""
        add_database_guild(guild)

    @bot.event
    async def on_member_join(member):
        """Adds a member to the database when they join a guild."""
        add_database_member(member)

    @bot.command()
    async def test(ctx, args):
        log_to_database(ctx.guild, 'Test log 1')

    # Load the cogs
    bot.load_extension('cogs.around_the_world')
    bot.load_extension('cogs.banned_words')
    bot.load_extension('cogs.counting')
    bot.load_extension('cogs.logs')
    bot.load_extension('cogs.member_leave')
    bot.load_extension('cogs.member_welcome')
    bot.load_extension('cogs.private_vc')
    bot.load_extension('cogs.reaction_role')

    # Run the Bot
    load_dotenv()
    bot.run(os.environ.get('BOT_TOKEN'))


if __name__ == '__main__':
    main()
