from __future__ import annotations

import discord
from discord.ext import commands

from core import Cog, Context
from models import VoiceChannel, VcConfig
from utils import emote


class VoiceControlPanel(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel, owner_id: int):
        super().__init__(timeout=None)
        self.channel = channel
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Only the channel owner can use these controls.", ephemeral=True)
        return True

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.Button):
        await self.channel.set_permissions(interaction.guild.default_role, connect=False)
        await VoiceChannel.filter(channel_id=self.channel.id).update(is_locked=True)
        await interaction.response.send_message("🔒 Channel locked. Only you can join.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, emoji="🔓", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: discord.Button):
        await self.channel.set_permissions(interaction.guild.default_role, connect=True)
        await VoiceChannel.filter(channel_id=self.channel.id).update(is_locked=False)
        await interaction.response.send_message("🔓 Channel unlocked. Everyone can join.", ephemeral=True)

    @discord.ui.button(label="Limit", style=discord.ButtonStyle.blurple, emoji="👤", row=0)
    async def limit_channel(self, interaction: discord.Interaction, button: discord.Button):
        modal = discord.ui.Modal(title="Set User Limit")
        limit = discord.ui.TextInput(label="Limit (0 = unlimited)", placeholder="Enter a number between 0 and 99", max_length=2)
        modal.add_item(limit)

        async def on_submit(modal_interaction: discord.Interaction):
            try:
                limit_val = int(limit.value.strip())
                if limit_val < 0 or limit_val > 99:
                    return await modal_interaction.response.send_message("Limit must be between 0 and 99.", ephemeral=True)
                await self.channel.edit(user_limit=limit_val)
                await VoiceChannel.filter(channel_id=self.channel.id).update(user_limit=limit_val)
                await modal_interaction.response.send_message(f"User limit set to {limit_val if limit_val > 0 else 'unlimited'}.", ephemeral=True)
            except ValueError:
                await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.grey, emoji="✏️", row=1)
    async def rename_channel(self, interaction: discord.Interaction, button: discord.Button):
        modal = discord.ui.Modal(title="Rename Channel")
        name = discord.ui.TextInput(label="New Name", placeholder="Enter new channel name", max_length=100)
        modal.add_item(name)

        async def on_submit(modal_interaction: discord.Interaction):
            new_name = name.value.strip()[:100]
            if not new_name:
                return await modal_interaction.response.send_message("Channel name cannot be empty.", ephemeral=True)
            await self.channel.edit(name=new_name)
            await VoiceChannel.filter(channel_id=self.channel.id).update(name=new_name)
            await modal_interaction.response.send_message(f"Channel renamed to: {new_name}", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.red, emoji="🚫", row=1)
    async def kick_user(self, interaction: discord.Interaction, button: discord.Button):
        members = [m for m in self.channel.members if m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("No one else in the channel to kick.", ephemeral=True)

        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]]
        select = discord.ui.Select(placeholder="Select user to kick", options=options)

        async def on_select(select_interaction: discord.Interaction):
            user_id = int(select.values[0])
            member = self.channel.guild.get_member(user_id)
            if member:
                await member.move_to(None)
                await select_interaction.response.send_message(f"Kicked {member.mention} from the channel.", ephemeral=True)
            else:
                await select_interaction.response.send_message("User not found.", ephemeral=True)

        select.callback = on_select
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select a user to kick:", view=view, ephemeral=True)

    @discord.ui.button(label="Transfer", style=discord.ButtonStyle.blurple, emoji="👑", row=2)
    async def transfer_owner(self, interaction: discord.Interaction, button: discord.Button):
        members = [m for m in self.channel.members if m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("No one else in the channel to transfer ownership.", ephemeral=True)

        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]]
        select = discord.ui.Select(placeholder="Select new owner", options=options)

        async def on_select(select_interaction: discord.Interaction):
            user_id = int(select.values[0])
            member = self.channel.guild.get_member(user_id)
            if member:
                await VoiceChannel.filter(channel_id=self.channel.id).update(owner_id=user_id)
                await select_interaction.response.send_message(f"Transferred ownership to {member.mention}.", ephemeral=True)
            else:
                await select_interaction.response.send_message("User not found.", ephemeral=True)

        select.callback = on_select
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select new owner:", view=view, ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("Deleting channel...", ephemeral=True)
        await VoiceChannel.filter(channel_id=self.channel.id).delete()
        await self.channel.delete()


class VoiceChannels(Cog, name="Voice"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel and after.channel.name == "➕ Create Channel":
            await self._create_voice_channel(member, after.channel)
        elif before.channel and before.channel.name.endswith("'s Room"):
            await self._check_empty_channel(before.channel)

        if after.channel:
            config = await VcConfig.get_or_none(guild_id=member.guild.id, channel_id=after.channel.id)
            if config and config.role_id:
                role = member.guild.get_role(config.role_id)
                if role and role not in member.roles:
                    await member.add_roles(role, reason="Voice channel role")
        if before.channel:
            config = await VcConfig.get_or_none(guild_id=member.guild.id, channel_id=before.channel.id)
            if config and config.role_id:
                role = member.guild.get_role(config.role_id)
                if role and role in member.roles:
                    await member.remove_roles(role, reason="Left voice channel")

    async def _create_voice_channel(self, member: discord.Member, create_channel: discord.VoiceChannel):
        existing = discord.utils.get(create_channel.category.voice_channels, name=f"{member.display_name}'s Room")
        if existing:
            await member.move_to(existing)
            return

        new_channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s Room",
            category=create_channel.category,
            overwrites={
                member.guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True, move_members=True),
            },
        )

        await VoiceChannel.create(
            guild_id=member.guild.id,
            channel_id=new_channel.id,
            owner_id=member.id,
            name=new_channel.name,
        )

        await member.move_to(new_channel)

        embed = discord.Embed(
            title="🎛️ Voice Control Panel",
            description="Use the buttons below to control your voice channel.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Channel Owner: {member.display_name}")

        view = VoiceControlPanel(new_channel, member.id)
        await new_channel.send(embed=embed, view=view)

    async def _check_empty_channel(self, channel: discord.VoiceChannel):
        if len(channel.members) == 0:
            await VoiceChannel.filter(channel_id=channel.id).delete()
            try:
                await channel.delete()
            except discord.NotFound:
                pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_voice(self, ctx: Context):
        """Setup the Join-to-Create voice system."""
        existing = discord.utils.get(ctx.guild.voice_channels, name="➕ Create Channel")
        if existing:
            return await ctx.send(f"Join-to-Create channel already exists: {existing.mention}")

        category = await ctx.guild.create_category("Voice Channels")
        create_channel = await ctx.guild.create_voice_channel(
            name="➕ Create Channel",
            category=category,
        )

        await VoiceChannel.create(
            guild_id=ctx.guild.id,
            channel_id=create_channel.id,
            owner_id=ctx.guild.owner_id,
            name=create_channel.name,
            is_locked=False,
        )

        embed = discord.Embed(
            title="🎙️ Join-to-Create Setup",
            description=f"Created voice channel: {create_channel.mention}\n\n"
            "Users joining this channel will get their own private voice channel.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def voicepanel(self, ctx: Context, channel: discord.VoiceChannel = None):
        """Send the voice control panel to a voice channel."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        if not channel:
            return await ctx.send("You must be in a voice channel or specify one.")

        embed = discord.Embed(
            title="🎛️ Voice Control Panel",
            description="Use the buttons below to control your voice channel.",
            color=discord.Color.blue(),
        )
        view = VoiceControlPanel(channel, ctx.author.id)
        await channel.send(embed=embed, view=view)
        await ctx.send(f"Voice panel sent to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def drag(self, ctx: Context, member: discord.Member, channel: discord.VoiceChannel):
        """Drag a user to a voice channel."""
        if not member.voice:
            return await ctx.error(f"{member.mention} is not in a voice channel.")
        await member.move_to(channel)
        await ctx.success(f"Dragged {member.mention} to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def pull(self, ctx: Context, member: discord.Member, channel: discord.VoiceChannel = None):
        """Pull a user to your voice channel."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        if not channel:
            return await ctx.error("You must be in a voice channel or specify one.")
        if not member.voice:
            return await ctx.error(f"{member.mention} is not in a voice channel.")
        await member.move_to(channel)
        await ctx.success(f"Pulled {member.mention} to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vckick(self, ctx: Context, member: discord.Member):
        """Kick a user from voice channel."""
        if not member.voice:
            return await ctx.error(f"{member.mention} is not in a voice channel.")
        await member.move_to(None)
        await ctx.success(f"Kicked {member.mention} from voice channel.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcmute(self, ctx: Context, member: discord.Member):
        """Server mute a user in voice channel."""
        if not member.voice:
            return await ctx.error(f"{member.mention} is not in a voice channel.")
        await member.edit(mute=True)
        await ctx.success(f"Muted {member.mention} in voice channel.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcunmute(self, ctx: Context, member: discord.Member):
        """Unmute a user in voice channel."""
        if not member.voice:
            return await ctx.error(f"{member.mention} is not in a voice channel.")
        await member.edit(mute=False)
        await ctx.success(f"Unmuted {member.mention} in voice channel.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcban(self, ctx: Context, member: discord.Member, channel: discord.VoiceChannel = None):
        """Ban a user from a voice channel."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        if not channel:
            return await ctx.error("You must be in a voice channel or specify one.")
        await channel.set_permissions(member, connect=False)
        if member.voice and member.voice.channel == channel:
            await member.move_to(None)
        await ctx.success(f"Banned {member.mention} from {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcunban(self, ctx: Context, member: discord.Member, channel: discord.VoiceChannel = None):
        """Unban a user from a voice channel."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        if not channel:
            return await ctx.error("You must be in a voice channel or specify one.")
        await channel.set_permissions(member, connect=None)
        await ctx.success(f"Unbanned {member.mention} from {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcmoveall(self, ctx: Context, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        """Move all users from one voice channel to another."""
        if not from_channel.members:
            return await ctx.error(f"No users in {from_channel.mention}.")
        for member in from_channel.members:
            await member.move_to(to_channel)
        await ctx.success(f"Moved all users from {from_channel.mention} to {to_channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vcrole(self, ctx: Context, channel: discord.VoiceChannel, role: discord.Role):
        """Set a role to be given when a user joins a voice channel."""
        config, _ = await VcConfig.get_or_create(guild_id=ctx.guild.id, channel_id=channel.id)
        config.role_id = role.id
        await config.save()
        await ctx.success(f"Set {role.mention} to be given when users join {channel.mention}")


async def setup(bot):
    await bot.add_cog(VoiceChannels(bot))
