import discord

from discord.ext import commands
from discord.errors import Forbidden, HTTPException
from utils.database import add_database_member, get_guild_data, log_to_database, update_database_guild
from utils.message import delete_message, get_message, send_message


class Counting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'leaderboard': self.leaderboard, 'lb': self.leaderboard,
            'reset': self.reset,
            'help': self.help
        }

    @commands.command()
    async def counting(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'help'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Deletes a message if it does not adhere to counting rules."""
        guild = message.guild

        # Return if the message is not in #counting
        if message.channel.name != 'counting' or message.author.bot:
            return

        # Delete the message if it is not an integer
        try:
            message_int = int(message.content)
        except ValueError:
            await delete_message(message)
            return

        # Get the last message sent in the channel
        try:
            history = message.channel.history(limit=2)
            last_message = (await history.flatten())[1]
            last_message_content = last_message.content
        except Forbidden as e:
            log_to_database(guild, f'[{e.status} {e.response.reason}] Did not have permission to get channel history.')
            return
        except HTTPException as e:
            log_to_database(guild, f'[{e.status} {e.response.reason}] Failed request to get channel history.')
            return

        # Return if the previous message was not an integer (this should not happen)
        try:
            last_int = int(last_message_content)
        except ValueError:
            await delete_message(message)
            log_to_database(guild, f'The previous message in #counting was not an integer.')
            return

        # Return if the message is not one more than the previous message
        if message_int != last_int+1:
            await delete_message(message)
            return
        
        # Get the guild data from the database
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return
        
        # Get the current count
        database_author = None
        member_data = guild_data['member_data']
        for member in member_data:
            if member['member_id'] == message.author.id:
                member['counted'] += 1
                break
        else:
            # Add the member to the database
            add_database_member(message.author)
            return

        # Update the database
        update_database_guild(
            guild,
            {"$set": {"member_data": member_data}},
            f'Failed to update count for member "{message.author.name}" (id={message.author.id}) to the database.'
        )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """Prevents editing."""
        channel = self.bot.get_channel(payload.channel_id)
        if channel.name != 'counting':
            return

        message = await get_message(channel, payload.message_id)
        await delete_message(message)

    @staticmethod
    async def leaderboard(ctx, args):
        """Shows the counting leaderboard."""
        guild = ctx.guild

        # Get the guild data from the database
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Get list of member scores
        score_pairs = []
        member_data = guild_data['member_data']
        for member in member_data:
            if discord.utils.get(guild.members, id=member['member_id']):
                score_pairs.append({
                    'member_id': member['member_id'],
                    'counted': member['counted']
                })
        score_pairs.sort(key=lambda x: x['counted'], reverse=True)

        # Get top ten
        top_ten = ''
        author_listed = False
        for i, score_pair in enumerate(score_pairs):
            
            member = discord.utils.get(guild.members, id=score_pair['member_id'])
            if member == ctx.author:
                author_listed = True
            
            if i < 10 or author_listed == False:

                name = member.nick or member.name
                score = score_pair['counted']
                top_ten += f'{i+1}. {name}: {score}\n'

                continue

            break

        # Create embed
        embed = discord.Embed(title='Counting Leaderboard', color=ctx.bot.embed_color)
        embed.add_field(name='***Top Counters***', value=top_ten, inline=True)

        # Send embed
        await send_message(ctx.channel, embed=embed)

    @staticmethod
    async def reset(ctx, args):
        """Resets the counting data."""
        guild = ctx.guild

        # Check if the member has adminstrator
        if not ctx.author.guild_permissions.administrator:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get the guild data from the database
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Set the count to 0 for every member
        member_data = guild_data['member_data']
        for member in member_data:
            member['counted'] = 0

        # Update the database
        updated = update_database_guild(
            guild,
            {"$set": {"member_data": member_data}},
            'Failed to reset the count database.'
        )
        if updated == False:
            return
        
        # Restart the counting channel
        counting = discord.utils.get(guild.text_channels, name='counting')
        if counting:
            await send_message(counting, '1')

        await send_message(ctx.channel, 'Counting data has successfully been reset.')

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Counting Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages a channel with the name [#counting].

        All messages that are not one number higher than the previous message will be deleted.
        The number of times a member sends a 'correct' message to the channel is tracked and ranked.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}counting help`
        Show this message.
        Required Permission: Everyone

        `{prefix}counting leaderboard`
        `{prefix}counting lb`
        Displays the current ranking for the counting channel
        Required Permission: Everyone

        `{prefix}counting reset`
        Resets the counting leaderboard. There is no way to recover this data.
        Required Permission: Administrator
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(Counting(bot))
