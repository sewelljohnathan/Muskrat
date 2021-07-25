import asyncio
import discord

from discord.ext import commands
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from utils.channel import convert_to_channel
from utils.database import get_guild_data, log_to_database, update_database_guild
from utils.message import delete_message, send_message
from utils.role import convert_to_role, give_member_role, remove_member_role


class ReactionRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'create': ReactionRole.create,
            'help': ReactionRole.help,
        }

    @commands.command(aliases=['rr'])
    async def reaction_role(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'help'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gives a role from a Reaction Role message."""
        await edit_member_role(
            guild=self.bot.get_guild(payload.guild_id), 
            payload=payload, 
            func=give_member_role
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Removes a role from a Reaction Role message."""
        await edit_member_role(
            guild=self.bot.get_guild(payload.guild_id), 
            payload=payload, 
            func=remove_member_role
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Deletes a Reaction Role from the database."""
        guild = self.bot.get_guild(payload.guild_id)

        # Get guild data
        guild_data = get_guild_data(guild)
        if guild_data is None:
            return

        # Edit the guild data document
        reaction_roles = guild_data['reaction_roles']
        for rr in reaction_roles:
            if rr['message_id'] == payload.message_id:
                
                reaction_roles.remove(rr)
                break
        else:
            return

        # Update the database
        update_database_guild(
            guild,
            {"$set": {"reaction_roles": reaction_roles}},
            'Failed to remove a reaction role.'
        )

    @staticmethod
    async def create(ctx, args):
        """Creates a new Reaction Role."""
        guild = ctx.guild

        # Check if the caller has permission
        if not ctx.author.guild_permissions.manage_messages:
            await send_message(ctx.channel, 'You don\'t have permission to use that command.')
            return

        # Get channel
        channel = await convert_to_channel(ctx, args)
        if channel is None:
            return

        # Get the message content
        message_content = await get_response(ctx, 'Type the message used to create the Reaction Role.')
        if message_content is None:
            await send_message(ctx.channel, 'Exiting Reaction Role creation.')
            return

        # Get the role-emoji pairs
        pairs = await get_pairs(ctx)
        if pairs is None:
            await send_message(ctx.channel, 'Exiting Reaction Role creation.')
            return

        # Create message
        message = await send_message(ctx.channel, message_content)
        if message is None:
            await send_message(ctx.channel, 'Failed to create message. See logs for more detail.')
            return

        # Add reactions
        successful = True
        for pair in pairs:
            emoji = pair['emoji']
            try:
                await message.add_reaction(emoji)
            except HTTPException as e:
                log_to_database(guild, f'[{e.status} {e.response.reason}] Failed to add a reaction "{emoji}".')
            except Forbidden as e:
                log_to_database(guild, f'[{e.status} {e.response.reason}] Did not have permission to add a reaction.')  
            except NotFound as e:
                log_to_database(guild, f'[{e.status} {e.response.reason}] Failed to find emoji {emoji}.')
            except InvalidArgument:
                log_to_database(guild, f'Invalid emoji "{emoji}".')
            else:
                continue
            
            successful = False
            break

        if successful == False:
            await delete_message(message)
            await send_message(ctx.channel, 'An error occured adding the reactions. See logs for more detail.')
            return
        
        # Update the database
        updated = update_database_guild(
            guild,
            {"$push": {"reaction_roles": { 
                "message_id": message.id,
                "role-emoji_pairs": pairs
            }}},
            'Failed to add a Reaction Role to the database.'
        )
        if updated == False:
            await delete_message(message)
            await send_message(ctx.channel, 'An error occured adding the Reaction Role to the database. See logs for more detail.')
            return

        # Send confirmation
        await send_message(ctx.channel, f'Reaction Role successfully created! Head to {channel.mention} to see it!')
        
    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Reaction Roles Help', color=ctx.bot.embed_color)

        description = '''
        This Cog manages Reaction Roles.

        When a member reacts to a message with a specific emoji, they will get a corresponding role set when the Reaction Role is created.
        A Reaction Role can be removed by simply deleting the message.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}rr help`
        Show this message.
        Required Permission: Everyone

        `{prefix}rr create [text channel]`
        Creates a new reaction role for [text channel]. 
        You will then be prompted to enter pairs of roles and the reaction emoji that will give them.
        Required Permission: Manage Messages
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        # Send embed
        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(ReactionRole(bot))


async def edit_member_role(guild, payload, func):
    """Edits a member's roles from a Reaction Role message."""
    # Get guild data
    guild_data = get_guild_data(guild)
    if guild_data is None:
        return

    # Get the member
    member = discord.utils.get(guild.members, id=payload.user_id)
    if member is None or member.bot:
        return

    for reaction_role in guild_data['reaction_roles']:
        if reaction_role['message_id'] != payload.message_id:
            continue
        
        for pair in reaction_role['role-emoji_pairs']:
            if pair['emoji'] == str(payload.emoji):

                role = discord.utils.get(guild.roles, id=pair['role_id'])
                if role is None:
                    continue
                
                await func(member, role)
                break
        else:
            continue

        break


async def get_response(ctx, prompt):
    """Get a response from a prompt."""
    await send_message(ctx.channel, prompt)

    try:
        response_message = await ctx.bot.wait_for('message', check=lambda x: x.author == ctx.author, timeout=120)
        response = response_message.content

    except asyncio.TimeoutError:
        return None

    return response


async def get_pairs(ctx):
    """Get all role-emoji pairs for a new Reaction Role message."""
    pairs = []
    while True:
        
        # Get response
        response = await get_response(ctx, 'What role and corresponding emoji would you like to add? Type `done` to finish.')
        if response is None:
            return None
        
        # Break if user is done
        if response.lower() == 'done':
            break
        
        # Parse role and emoji
        try:
            raw_role, emoji = response.split(' ')
        except ValueError:
            await send_message(ctx.channel, 'Could not parse role and emoji pair.')
            continue

        # Get role
        role = await convert_to_role(ctx, raw_role)
        if role is None:
            await send_message(ctx.channel, f'Failed to parse "{raw_role}" as a role.')
            continue

        # Append pair
        pairs.append({
            'role_id': role.id,
            'emoji': emoji
        })

    return pairs
