from discord.ext import commands
from discord.ext.commands.errors import BadArgument, CommandError
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.channel import CategoryChannel, TextChannel, VoiceChannel
from discord.guild import Guild
from discord.permissions import PermissionOverwrite
from typing import Union
from utils.database import log_to_database


async def delete_channel(channel: Union[VoiceChannel, TextChannel], *, reason=None) -> None:
    """Wrapper for discord.py channel.delete()"""
    try:
        await channel.delete(reason)
    except Forbidden as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Did not have permission to delete a channel.')
    except NotFound as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] A channel "{channel.name}" (id={channel.id}) could not be found.')
    except HTTPException as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Failed to delete a channel.')


async def create_voice_channel(guild: Guild, name: str, category: CategoryChannel, overwrites: PermissionOverwrite) -> VoiceChannel:
    """
    Wrapper for discord.py channel.create_voice_channel() 
    
    Returns the VoiceChannel or None.
    """
    try:
        voice_channel = await guild.create_voice_channel(
            name=name,
            category=category,
            overwrites=overwrites
        )
    except Forbidden as e:
        log_to_database(guild, f'[{e.status} {e.response.reason}] Did not have permission to create a channel.')
        return None
    except HTTPException as e:
        log_to_database(guild, f'[{e.status} {e.response.reason}] Failed to create a channel.')    
        return None  
    except InvalidArgument:
        log_to_database(guild, 'Failed to create a voice channel because overwrite information was not in proper form (Contact Developer).')   
        return None

    return voice_channel


async def convert_to_channel(ctx, arg) -> TextChannel:
    """
    Wrapper for discord.py commands.TextChannelConverter().convert()

    Returns the TextChannel or None.
    """
    try:
        channel = await commands.TextChannelConverter().convert(ctx, arg)
    except CommandError:
        return None
    except BadArgument:
        return None

    return channel

