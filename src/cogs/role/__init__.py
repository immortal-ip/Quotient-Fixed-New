from __future__ import annotations

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView, role_command_check
from cogs.mod.views.role import RoleRevertButton
from models import RoleAlias
from utils import ActionReason, MemberID, emote, plural


class RoleCog(Cog, name="Role Management"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        invoke_without_command=True,
        aliases=["addrole", "giverole"],
        extras={"examples": ["role @role @user1 @user2 @user3 ..."]},
    )
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.cooldown(4, 1, type=commands.BucketType.guild)
    @role_command_check()
    async def role(self, ctx: Context, role: discord.Role, members: commands.Greedy[discord.Member]):
        """Add a role to one or multiple users."""

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        if not members:
            members = ctx.guild.members

            prompt = await ctx.prompt("No members were specified, do you want to add the role to all members?")
            if not prompt:
                return await ctx.simple(
                    f"Alright, Aborting. If you wish to add the role to limited users, do:\n\n`{ctx.prefix}role @role @user1 @user2 @user3 ...`"
                )

        m = await ctx.simple(f"{emote.loading} Adding {role.mention} to {plural(members):member|members}.")

        for member in members:
            if role not in member.roles:
                await member.add_roles(role, reason=reason)

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Added {role.mention} to {plural(members):member|members}.\n\n"
            "```If you cannot see the role in any of the user's profile, just restart your discord app or check audit log.```",
            view=_view,
        )

    @role.command(name="humans", extras={"examples": ["role humans @role", "role humans role_id"]})
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.cooldown(5, 1, type=commands.BucketType.guild)
    @role_command_check()
    async def role_humans(self, ctx: Context, role: discord.Role):
        """Add a role to all human users."""

        members = [m for m in ctx.guild.members if all([not role in m.roles, not m.bot])]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be added to all {plural(members):human|humans} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Adding {role.mention} to {plural(members):human|humans}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.add_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully added {role.mention} to {plural(success):human|humans}. (Failed: {failed})", view=_view
        )

    @role.command(name="bots", extras={"examples": ["role bots @role", "role bots role_id"]})
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def role_bots(self, ctx: Context, role: discord.Role):
        """Add a role to all bot users."""
        members = [m for m in ctx.guild.members if all([not role in m.roles, m.bot])]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be added to all {plural(members):bot|bots} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Adding {role.mention} to {plural(members):bot|bots}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.add_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully added {role.mention} to {plural(success):bot|bots}. (Failed: {failed})", view=_view
        )

    @role.command(name="all", extras={"examples": ["role all @role", "role all role_id"]})
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def role_all(self, ctx: Context, role: discord.Role):
        """Add a role to everyone on the server"""

        members = [m for m in ctx.guild.members if not role in m.roles]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be added to all {plural(members):user|users} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Adding {role.mention} to {plural(members):user|users}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.add_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully added {role.mention} to {plural(success):user|users}. (Failed: {failed})", view=_view
        )

    @role.command(name="r")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def role_toggle(self, ctx: Context, role: discord.Role, member: discord.Member):
        """Toggle role for a member."""
        if role in member.roles:
            await member.remove_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Removed {role.mention} from {member.mention}")
        else:
            await member.add_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Added {role.mention} to {member.mention}")

    @role.command(name="n")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def role_by_name(self, ctx: Context, role_name: str, member: discord.Member):
        """Add/remove role by name."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            return await ctx.error(f"Role `{role_name}` not found.")

        if role in member.roles:
            await member.remove_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Removed {role.mention} from {member.mention}")
        else:
            await member.add_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Added {role.mention} to {member.mention}")

    @role.command(name="alias")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_alias(self, ctx: Context, role: discord.Role, alias_name: str):
        """Create a shortcut alias for a role."""
        existing = await RoleAlias.get_or_none(guild_id=ctx.guild.id, alias=alias_name.lower())
        if existing:
            return await ctx.error(f"Alias `{alias_name}` already exists for another role.")

        await RoleAlias.create(guild_id=ctx.guild.id, role_id=role.id, alias=alias_name.lower())
        await ctx.success(f"Alias `{alias_name}` created for {role.mention}")

    @role.command(name="give")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def role_give(self, ctx: Context, alias_name: str, member: discord.Member):
        """Assign a role using its alias."""
        record = await RoleAlias.get_or_none(guild_id=ctx.guild.id, alias=alias_name.lower())
        if not record:
            return await ctx.error(f"Alias `{alias_name}` not found.")

        role = ctx.guild.get_role(record.role_id)
        if role is None:
            return await ctx.error(f"Role not found. The alias may be invalid.")

        if role in member.roles:
            await member.remove_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Removed {role.mention} from {member.mention}")
        else:
            await member.add_roles(role, reason=f"Action done by {ctx.author}")
            await ctx.success(f"Added {role.mention} to {member.mention}")

    @role.command(name="remove_alias")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_remove_alias(self, ctx: Context, alias_name: str):
        """Remove a role alias."""
        record = await RoleAlias.get_or_none(guild_id=ctx.guild.id, alias=alias_name.lower())
        if not record:
            return await ctx.error(f"Alias `{alias_name}` not found.")

        await record.delete()
        await ctx.success(f"Alias `{alias_name}` removed.")

    @role.command(name="list_aliases")
    @commands.has_guild_permissions(manage_roles=True)
    async def role_list_aliases(self, ctx: Context):
        """View all configured role aliases."""
        records = await RoleAlias.filter(guild_id=ctx.guild.id)
        if not records:
            return await ctx.error("No role aliases configured.")

        lines = []
        for rec in records:
            role = ctx.guild.get_role(rec.role_id)
            role_name = role.mention if role else "Deleted Role"
            lines.append(f"`{rec.alias}` → {role_name}")

        embed = self.bot.embed(ctx, title="Role Aliases", description="\n".join(lines))
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=["removerole", "takerole"])
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def rrole(self, ctx: Context, role: discord.Role, members: commands.Greedy[discord.Member]):
        """Remove a role from one or multiple users."""
        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        if not members:
            members = [m for m in ctx.guild.members if role in m.roles]

            prompt = await ctx.prompt("No members were specified, do you want to remove the role from all members?")
            if not prompt:
                return await ctx.simple(
                    f"Alright, Aborting. If you wish to remove the role from limited users, do:\n\n`{ctx.prefix}rrole @role @user1 @user2 @user3 ...`"
                )

        m = await ctx.simple(f"{emote.loading} Removing {role.mention} from {plural(members):member|members}.")

        for member in members:
            await member.remove_roles(role, reason=reason)

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members, take_role=False))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Removed {role.mention} from {plural(members):member|members}.",
            view=_view,
        )

    @rrole.command(name="humans")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def rrole_humans(self, ctx: Context, role: discord.Role):
        """Remove a role from all human users."""

        members = [m for m in ctx.guild.members if all([role in m.roles, not m.bot])]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be removed from all {plural(members):human|humans} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Remove {role.mention} from {plural(members):human|humans}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.remove_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members, take_role=False))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully removed {role.mention} from {plural(success):human|humans}. (Failed: {failed})", view=_view
        )

    @rrole.command(name="bots")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def rrole_bots(self, ctx: Context, role: discord.Role):
        """Remove a role from all the bots."""
        members = [m for m in ctx.guild.members if all([role in m.roles, m.bot])]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be removed from all {plural(members):bot|bots} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Remove {role.mention} from {plural(members):bot|bots}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.remove_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members, take_role=False))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully removed {role.mention} from {plural(success):bot|bots}. (Failed: {failed})", view=_view
        )

    @rrole.command(name="all")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_command_check()
    async def rrole_all(self, ctx: Context, role: discord.Role):
        """Remove a role from everyone on the server."""
        members = [m for m in ctx.guild.members if role in m.roles]

        prompt = await ctx.prompt(
            title="Are you sure you want to continue?",
            message=f"{role.mention} will be removed from all {plural(members):user|users} in the server.",
        )

        if not prompt:
            return await ctx.success("Alright, Aborting.")

        reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
        m = await ctx.simple(f"{emote.loading} Removing {role.mention} from {plural(members):user|users}.")

        success, failed = 0, 0

        for member in members:
            try:
                await member.remove_roles(role, reason=reason)
                success += 1
            except discord.HTTPException:
                failed += 1

        _view = QuotientView(ctx)
        _view.add_item(RoleRevertButton(ctx, role=role, members=members, take_role=False))

        await ctx.safe_delete(m)
        _view.message = await ctx.success(
            f"Successfully removed {role.mention} from {plural(success):user|users}. (Failed: {failed})", view=_view
        )

    @commands.group(name="humanrole", invoke_without_command=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def humanrole(self, ctx: Context):
        """Manage roles for all human users."""
        await ctx.send_help(ctx.command)

    @humanrole.command(name="add")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def humanrole_add(self, ctx: Context, role: discord.Role):
        """Add a role to all human users."""
        members = [m for m in ctx.guild.members if role not in m.roles and not m.bot]
        if not members:
            return await ctx.error(f"No humans need {role.mention}.")

        prompt = await ctx.prompt(
            message=f"Add {role.mention} to {len(members)} humans?",
        )
        if not prompt:
            return await ctx.success("Aborted.")

        success, failed = 0, 0
        for member in members:
            try:
                await member.add_roles(role, reason=f"Action done by {ctx.author}")
                success += 1
            except discord.HTTPException:
                failed += 1

        await ctx.success(f"Added {role.mention} to {success} humans. (Failed: {failed})")

    @humanrole.command(name="remove")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def humanrole_remove(self, ctx: Context, role: discord.Role):
        """Remove a role from all human users."""
        members = [m for m in ctx.guild.members if role in m.roles and not m.bot]
        if not members:
            return await ctx.error(f"No humans have {role.mention}.")

        prompt = await ctx.prompt(
            message=f"Remove {role.mention} from {len(members)} humans?",
        )
        if not prompt:
            return await ctx.success("Aborted.")

        success, failed = 0, 0
        for member in members:
            try:
                await member.remove_roles(role, reason=f"Action done by {ctx.author}")
                success += 1
            except discord.HTTPException:
                failed += 1

        await ctx.success(f"Removed {role.mention} from {success} humans. (Failed: {failed})")

    @commands.group(name="botrole", invoke_without_command=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def botrole(self, ctx: Context):
        """Manage roles for all bots."""
        await ctx.send_help(ctx.command)

    @botrole.command(name="add")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def botrole_add(self, ctx: Context, role: discord.Role):
        """Add a role to all bots."""
        members = [m for m in ctx.guild.members if role not in m.roles and m.bot]
        if not members:
            return await ctx.error(f"No bots need {role.mention}.")

        prompt = await ctx.prompt(
            message=f"Add {role.mention} to {len(members)} bots?",
        )
        if not prompt:
            return await ctx.success("Aborted.")

        success, failed = 0, 0
        for member in members:
            try:
                await member.add_roles(role, reason=f"Action done by {ctx.author}")
                success += 1
            except discord.HTTPException:
                failed += 1

        await ctx.success(f"Added {role.mention} to {success} bots. (Failed: {failed})")

    @botrole.command(name="remove")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def botrole_remove(self, ctx: Context, role: discord.Role):
        """Remove a role from all bots."""
        members = [m for m in ctx.guild.members if role in m.roles and m.bot]
        if not members:
            return await ctx.error(f"No bots have {role.mention}.")

        prompt = await ctx.prompt(
            message=f"Remove {role.mention} from {len(members)} bots?",
        )
        if not prompt:
            return await ctx.success("Aborted.")

        success, failed = 0, 0
        for member in members:
            try:
                await member.remove_roles(role, reason=f"Action done by {ctx.author}")
                success += 1
            except discord.HTTPException:
                failed += 1

        await ctx.success(f"Removed {role.mention} from {success} bots. (Failed: {failed})")


async def setup(bot):
    await bot.add_cog(RoleCog(bot))
