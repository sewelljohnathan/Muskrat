from discord.ext import commands
from discord.errors import Forbidden, HTTPException
from utils.database import add_database_member, get_guild_data, log_to_database, update_database_guild
from utils.message import delete_message


class OnMessage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Filter messages."""
        if message.channel.name == 'around-the-world':
            self.around_the_world(message)
        
        elif message.channel.name == 'counting':
            self.counting(message)

        else:
            self.banned_words(message)
        
    async def around_the_world(self, message):
        """Filter messages in #around-the-world."""
        if message.channel.name != 'around-the-world':
            return

        if message.content.lower() != 'around the world':
            await delete_message(message)        

    async def banned_words(self, message):
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

    async def counting(self, message):
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


def setup(bot):
    bot.add_cog(OnMessage(bot))
