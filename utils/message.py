from discord.channel import TextChannel
from discord.errors import Forbidden, HTTPException, NotFound
from discord.message import Message
from utils.database import log_to_database


async def send_message(channel: TextChannel, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None, reference=None, mention_author=None) -> Message:
    """
    Wrapper for discord.py channel.send() 
    
    Returns the Message or None.
    """
    try:
        message = await channel.send(
            content=content, 
            tts=tts, 
            embed=embed, 
            file=file, 
            files=files, 
            delete_after=delete_after, 
            nonce=nonce, 
            allowed_mentions=allowed_mentions, 
            reference=reference, 
            mention_author=mention_author
        )
    except HTTPException as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Failed to send a message.')
        return None
    except Forbidden as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Did not have permission to send a message.')
        return None

    return message


async def delete_message(message: Message) -> None:
    """Wrapper for discord.py message.delete()"""
    try:
        await message.delete()
    except Forbidden as e:
        log_to_database(message.guild, f'[{e.status} {e.response.reason}] Did not have permission to delete a message.')
    except NotFound as e:
        log_to_database(message.guild, f'[{e.status} {e.response.reason}] A message "{message.content}" (id={message.id}) could not be found.')
    except HTTPException as e:
        log_to_database(message.guild, f'[{e.status} {e.response.reason}] Failed to delete a message.')


async def get_message(channel: TextChannel, message_id: int) -> Message:
    """
    Wrapper for discord.py channel.fetch_message() 
    
    Returns the Message or None.
    """
    try:
        message = await channel.fetch_message(message_id)
    except NotFound as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] A message (id={message_id}) could not be found.')
        return None
    except Forbidden as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Did not have permission to get a message (id={message_id}).')
        return None
    except HTTPException as e:
        log_to_database(channel.guild, f'[{e.status} {e.response.reason}] Failed to get a message (id={message_id}).')
        return None

    return message

