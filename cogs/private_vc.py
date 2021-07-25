import discord

from discord.ext import commands
from utils.channel import create_voice_channel, delete_channel
from utils.message import send_message


class PrivateVC(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.subcommands = {
            'help': self.help
        }

    @commands.command(aliases=['pvc'])
    async def private_vc(self, ctx, subcommand=None, *, args=None):
        """Manages subcommands."""
        subcommand = subcommand or 'help'
        if subcommand in self.subcommands:
            await self.subcommands[subcommand](ctx, args)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Creates and deletes private Voice Channels."""
        guild = member.guild

        # Get potential private vc names
        private_vc_name = f'Private - {member.nick or member.name}'
        waiting_vc_name = f'Waiting - {member.nick or member.name}'

        # Delete private channels if the owner leaves
        if before.channel and before.channel.name == private_vc_name:
            
            private_vc = discord.utils.get(guild.channels, name=private_vc_name)
            waiting_vc = discord.utils.get(guild.channels, name=waiting_vc_name)
            if private_vc:
                await delete_channel(private_vc)
            if waiting_vc:
                await delete_channel(waiting_vc)

        # Create private channels
        if after.channel and after.channel.name == 'Create Private VC':
            
            # Create private channel overwrites
            default_overwrite = discord.PermissionOverwrite(view_channel=False)
            member_overwrite = discord.PermissionOverwrite(
                view_channel=True,
                move_members=True
            )

            # Create private voice channel
            private_vc = await create_voice_channel(
                guild=member.guild,
                name=private_vc_name,
                category=after.channel.category,
                overwrites={member: member_overwrite, guild.default_role: default_overwrite}
            )
            if private_vc is None:
                return
            
            # Create waiting voice channel
            waiting_vc = await create_voice_channel(
                guild=member.guild,
                name=waiting_vc_name,
                category=after.channel.category,
                overwrites={member: member_overwrite}
            )
            if waiting_vc is None:
                await delete_channel(private_vc)
                return

            # Move member to their private vc
            await member.move_to(private_vc)

    @staticmethod
    async def help(ctx, args):
        """Help Command."""
        # Create embed
        embed = discord.Embed(title='Private VC Help', color=ctx.bot.embed_color)
        description = '''
        This Cog manages private voice chat channels.

        When a member joins a voice channel with the name 'Create Private VC', two new voice channels are created.
        The first is titled 'Private - [creator name]' and can only be seen by those in it.
        The second is titled 'Waiting - [creator name]' and can be seen by any member.

        The creator of the voice channel can drag anyone from the 'Waiting' channel into the 'Private' channel.
        When the creator leaves the 'Private' channel, both are automatically deleted.
        '''
        embed.add_field(name='***Description***', value=description, inline=True)

        prefix = ctx.prefix
        command_list = f'''
        `{prefix}pvc help`
        Show this message.
        Required Permission: Everyone
        '''
        embed.add_field(name='***Commands***', value=command_list, inline=False)

        await send_message(ctx.channel, embed=embed)


def setup(bot):
    bot.add_cog(PrivateVC(bot))
