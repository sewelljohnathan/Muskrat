from discord.ext import commands
from discord.ext.commands.errors import BadArgument, CommandError
from discord.errors import Forbidden, HTTPException
from discord.member import Member
from discord.role import Role
from utils.database import log_to_database


async def convert_to_role(ctx, arg) -> Role:
    """
    Wrapper for discord.py commands.RoleConverter().convert(). 
    
    Returns the Role or None
    """
    try:
        role = await commands.RoleConverter().convert(ctx, arg)
    except CommandError:
        return None
    except BadArgument:
        return None

    return role


async def give_member_role(member: Member, *roles: list[Role]) -> None:
    """Wrapper for discord.py member.add_roles()"""
    try:
        await member.add_roles(*roles)
    except Forbidden as e:
        log_to_database(member.guild, f'[{e.status} {e.response.reason}] Did not have permission to add roles.')
    except HTTPException as e:
        log_to_database(member.guild, f'[{e.status} {e.response.reason}] Failed to add roles.')


async def remove_member_role(member: Member, *roles: list[Role]) -> None:
    """Wrapper for discord.py member.remove_roles()"""
    try:
        await member.remove_roles(*roles)
    except Forbidden as e:
        log_to_database(member.guild, f'[{e.status} {e.response.reason}] Did not have permission to remove roles.')
    except HTTPException as e:
        log_to_database(member.guild, f'[{e.status} {e.response.reason}] Failed to remove roles.')  

