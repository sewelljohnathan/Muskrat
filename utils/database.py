from logging import error
import os
import datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from discord.guild import Guild
from discord.member import Member


def get_database() -> Database:
    """Returns the MongoDB database or None."""
    load_dotenv()
    mongo_client = MongoClient(os.environ.get('MONGO_URI'))
    if mongo_client is None:
        return None

    return mongo_client['database']


def get_guild_data(guild: Guild):
    """
    Wrapper for MongoDB collection.find_one() in the 'guilds' collection.
    
    Returns the document or None.
    """   
    guild_data = get_database()['guilds'].find_one({"guild_id": guild.id})
    if guild_data is None:
        log_to_database(guild, f'Could not find guild data.')
        return None
    
    return guild_data


def update_database_guild(guild: Guild, update, failure_message: str, upsert=False, bypass_document_validation=False, collation=None, array_filters=None, hint=None, session=None) -> bool:
    """
    Wrapper for MongoDB collection.update_one() in the 'guilds' collection.
    
    Returns True if successful and False is unsuccessful.
    """
    # Update the database
    update_result = get_database()['guilds'].update_one(
        filter={"guild_id": guild.id}, 
        update=update,
        upsert=upsert,
        bypass_document_validation=bypass_document_validation,
        collation=collation,
        array_filters=array_filters,
        hint=hint,
        session=session
    )

    # Check if the update succeeded
    if update_result.acknowledged == False:     
        log_to_database(guild, failure_message)
        return False

    return True


def log_to_database(guild: Guild, *args, sep=' ') -> None:
    """Logs text to the database."""
    # Get the timestamp
    timestamp = datetime.datetime.now().strftime("%d %b. %Y %H:%M:%S")

    # Get the log text
    log_text = ''
    for i, arg in enumerate(args):
        log_text += str(arg)
        if i < len(args)-1:
            log_text += sep
    log_output = f'[{timestamp}] {log_text}'

    # Add the log to the database
    print(log_output)
    update_database_guild(
        guild,
        {"$push": {"logs": log_output}},
        'Failed to push a log to the database.'
    )


def add_database_member(member: Member) -> bool:
    """
    Adds a member to the database. 
    
    Returns True if successful, and False if unsuccessful.
    """
    # Update database
    updated = update_database_guild(
        member.guild,
        {"$push": {"member_data": {
            "member_id": member.id,
            "counted": 0
        }}},
        f'Failed to add member "{member.name}" (id={member.id}) to the database.'
    )
    
    return updated


def add_database_guild(guild: Guild) -> bool:
    """
    Adds a guild to the database. 
    
    Returns True if successful, and False if unsuccessful.
    """
    update_result = get_database()['guilds'].insert_one({
        "guild_id": guild.id,
        "welcome_channel_id": 0,
        "welcome_message": "",
        "welcome_role_id": guild.default_role.id,
        "leave_channel_id": 0,
        "banned_words": [],
        "reaction_roles": [],
        "member_data": [],
        "logs": []
    })
    # Check if the update succeeded
    if update_result.acknowledged == False:     
        print(f'Failed to add guild "{guild.name}" (id={guild.id}) to the database.')
    
    return update_result
