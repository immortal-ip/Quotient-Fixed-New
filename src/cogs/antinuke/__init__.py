from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import Antinuke


class AntinukeSetupView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=180)
        self.ctx = ctx

    async def get_config(self):
        config, _ = await Antinuke.get_or_create(guild_id=self.ctx.guild.id)
        return config

    @discord.ui.button(label="Toggle", style=discord.ButtonStyle.green)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        config.enabled = not config.enabled
        await config.save()
        await interaction.edit_original_response(content=f"Antinuke is now **{'enabled' if config.enabled else 'disabled'}**.")

    @discord.ui.button(label="Log Channel", style=discord.ButtonStyle.blurple)
    async def set_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send the log channel. Mention it or send the channel ID.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        channel = None
        if msg.channel_mentions:
            channel = msg.channel_mentions[0]
        else:
            try:
                channel = self.ctx.guild.get_channel(int(msg.content.strip()))
            except ValueError:
                pass

        if channel is None or not isinstance(channel, discord.TextChannel):
            return await interaction.edit_original_response(content="Invalid channel.")

        config.log_channel_id = channel.id
        await config.save()
        await interaction.edit_original_response(content=f"Log channel set to {channel.mention}")

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.blurple)
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Mention a user to add/remove from whitelist.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        if not msg.mentions:
            return await interaction.edit_original_response(content="Please mention a user.")

        user = msg.mentions[0]
        whitelist = config.whitelist or []
        if user.id in whitelist:
            whitelist.remove(user.id)
            await interaction.edit_original_response(content=f"Removed {user.mention} from whitelist.")
        else:
            whitelist.append(user.id)
            await interaction.edit_original_response(content=f"Added {user.mention} to whitelist.")

        config.whitelist = whitelist
        await config.save()

    @discord.ui.button(label="Punishment", style=discord.ButtonStyle.blurple)
    async def punishment(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send punishment type: `ban` or `kick` or `none`", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        punishment = msg.content.strip().lower()
        if punishment not in ("ban", "kick", "none"):
            return await interaction.edit_original_response(content="Invalid punishment. Use `ban`, `kick`, or `none`.")

        config.punishment = punishment
        await config.save()
        await interaction.edit_original_response(content=f"Punishment set to `{punishment}`")


class AntinukeCog(Cog, name="Antinuke"):
    def __init__(self, bot):
        self.bot = bot
        self.action_tracker: dict[int, dict[str, list[datetime]]] = {}
        self.bot_invoker: dict[int, dict[int, int]] = {}
        self.locks: dict[int, asyncio.Lock] = {}

    async def get_config(self, guild_id: int) -> Antinuke:
        config, _ = await Antinuke.get_or_create(guild_id=guild_id)
        return config

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        return self.locks[guild_id]

    async def log_action(self, guild: discord.Guild, content: str):
        config = await self.get_config(guild.id)
        if not config.log_channel_id:
            return
        channel = guild.get_channel(config.log_channel_id)
        if channel is None:
            return
        embed = discord.Embed(title="⚠️ Antinuke Alert", description=content, color=discord.Color.red(), timestamp=datetime.utcnow())
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def _is_immune(self, guild: discord.Guild, user_id: int) -> bool:
        if user_id == guild.owner_id:
            return True
        if user_id == guild.me.id:
            return True
        config = await self.get_config(guild.id)
        if user_id in (config.whitelist or []):
            return True
        member = guild.get_member(user_id)
        if member and member.top_role >= guild.me.top_role:
            return True
        return False

    async def _punish(self, guild: discord.Guild, user_id: int, reason: str):
        async with self._get_lock(guild.id):
            config = await self.get_config(guild.id)
            if await self._is_immune(guild, user_id):
                return
            config.actioned += 1
            await config.save()
            member = guild.get_member(user_id)
            if member is None:
                return
            if config.punishment == "ban":
                try:
                    await guild.ban(member, reason=f"Antinuke: {reason}")
                except discord.Forbidden:
                    pass
            elif config.punishment == "kick":
                try:
                    await member.kick(reason=f"Antinuke: {reason}")
                except discord.Forbidden:
                    pass

    async def _record_action(self, guild_id: int, user_id: int, action: str):
        now = datetime.utcnow()
        tracker = self.action_tracker.setdefault(guild_id, {})
        user_actions = tracker.setdefault(str(user_id), {})
        times = user_actions.setdefault(action, [])
        times.append(now)
        cutoff = now - timedelta(seconds=10)
        times[:] = [t for t in times if t > cutoff]

    async def _check_threshold(self, guild_id: int, user_id: int, action: str, threshold: int) -> bool:
        tracker = self.action_tracker.get(guild_id, {})
        user_actions = tracker.get(str(user_id), {})
        times = user_actions.get(action, [])
        return len(times) >= threshold

    async def _resolve_bot_invoker(self, guild: discord.Guild, bot_id: int) -> Optional[int]:
        try:
            entry = next((e async for e in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add)), None)
        except discord.Forbidden:
            return None
        if entry and entry.user and entry.target_id == bot_id:
            return entry.user.id
        return None

    async def _get_actor(self, guild: discord.Guild, user_id: Optional[int], target: Optional[discord.abc.Snowflake]) -> Optional[int]:
        if user_id and not await self._is_immune(guild, user_id):
            return user_id
        if target and hasattr(target, "id"):
            tid = getattr(target, "id", None)
            if tid and tid in self.bot_invoker.get(guild.id, {}):
                return self.bot_invoker[guild.id].get(tid)
        if target and hasattr(target, "owner_id"):
            return getattr(target, "owner_id", None)
        return None

    @Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if not isinstance(channel, discord.TextChannel) and not isinstance(channel, discord.VoiceChannel):
            return
        try:
            entry = next((e async for e in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(channel.guild, entry.user.id, channel)
        if not actor:
            return
        config = await self.get_config(channel.guild.id)
        if not config.enabled or not config.anti_channel:
            return
        await self._record_action(channel.guild.id, actor, "channel_create")
        if await self._check_threshold(channel.guild.id, actor, "channel_create", max(1, config.channel_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(channel.guild, f"**{channel.guild.get_member(actor) or actor}** created mass channels.\nThreshold: {config.channel_threshold}")
            await self._punish(channel.guild, actor, "Mass channel create detected")
            try:
                await channel.delete(reason="Antinuke: Mass channel create")
            except discord.Forbidden:
                pass

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        try:
            entry = next((e async for e in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(channel.guild, entry.user.id, channel)
        if not actor:
            return
        config = await self.get_config(channel.guild.id)
        if not config.enabled or not config.anti_channel:
            return
        await self._record_action(channel.guild.id, actor, "channel_delete")
        if await self._check_threshold(channel.guild.id, actor, "channel_delete", max(1, config.channel_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(channel.guild, f"**{channel.guild.get_member(actor) or actor}** deleted mass channels.\nThreshold: {config.channel_threshold}")
            await self._punish(channel.guild, actor, "Mass channel delete detected")

    @Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        try:
            entry = next((e async for e in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(role.guild, entry.user.id, role)
        if not actor:
            return
        config = await self.get_config(role.guild.id)
        if not config.enabled or not config.anti_role:
            return
        await self._record_action(role.guild.id, actor, "role_create")
        if await self._check_threshold(role.guild.id, actor, "role_create", max(1, config.role_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(role.guild, f"**{role.guild.get_member(actor) or actor}** created mass roles.\nThreshold: {config.role_threshold}")
            await self._punish(role.guild, actor, "Mass role create detected")
            try:
                await role.delete(reason="Antinuke: Mass role create")
            except discord.Forbidden:
                pass

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        try:
            entry = next((e async for e in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(role.guild, entry.user.id, role)
        if not actor:
            return
        config = await self.get_config(role.guild.id)
        if not config.enabled or not config.anti_role:
            return
        await self._record_action(role.guild.id, actor, "role_delete")
        if await self._check_threshold(role.guild.id, actor, "role_delete", max(1, config.role_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(role.guild, f"**{role.guild.get_member(actor) or actor}** deleted mass roles.\nThreshold: {config.role_threshold}")
            await self._punish(role.guild, actor, "Mass role delete detected")

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Optional[discord.User] = None):
        try:
            entry = next((e async for e in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(guild, entry.user.id, None)
        if not actor:
            return
        config = await self.get_config(guild.id)
        if not config.enabled or not config.anti_ban:
            return
        await self._record_action(guild.id, actor, "ban")
        if await self._check_threshold(guild.id, actor, "ban", max(1, config.ban_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(guild, f"**{guild.get_member(actor) or actor}** banned mass members.\nThreshold: {config.ban_threshold}")
            await self._punish(guild, actor, "Mass ban detected")

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        try:
            entry = next((e async for e in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        if entry.target and entry.target.id != member.id:
            return
        actor = await self._get_actor(guild, entry.user.id, member)
        if not actor:
            return
        config = await self.get_config(guild.id)
        if not config.enabled or not config.anti_kick:
            return
        await self._record_action(guild.id, actor, "kick")
        if await self._check_threshold(guild.id, actor, "kick", max(1, config.kick_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(guild, f"**{guild.get_member(actor) or actor}** kicked mass members.\nThreshold: {config.kick_threshold}")
            await self._punish(guild, actor, "Mass kick detected")

    @Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        try:
            entry = next((e async for e in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create)), None)
            if not entry:
                entry = next((e async for e in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_delete)), None)
        except discord.Forbidden:
            return
        if not entry or not entry.user:
            return
        actor = await self._get_actor(channel.guild, entry.user.id, None)
        if not actor:
            return
        config = await self.get_config(channel.guild.id)
        if not config.enabled or not config.anti_webhook:
            return
        await self._record_action(channel.guild.id, actor, "webhook")
        if await self._check_threshold(channel.guild.id, actor, "webhook", max(1, config.webhook_threshold)):
            config.detected += 1
            await config.save()
            await self.log_action(channel.guild, f"**{channel.guild.get_member(actor) or actor}** spammed webhooks.\nThreshold: {config.webhook_threshold}")
            await self._punish(channel.guild, actor, "Webhook spam detected")

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            invoker = await self._resolve_bot_invoker(member.guild, member.id)
            if invoker:
                self.bot_invoker.setdefault(member.guild.id, {})[member.id] = invoker

            try:
                entry = next((e async for e in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add)), None)
            except discord.Forbidden:
                return
            if not entry or not entry.user:
                return
            actor = await self._get_actor(member.guild, entry.user.id, member)
            if not actor:
                return
            config = await self.get_config(member.guild.id)
            if not config.enabled or not config.anti_bot:
                return
            await self._record_action(member.guild.id, actor, "bot_add")
            if await self._check_threshold(member.guild.id, actor, "bot_add", max(1, config.bot_threshold)):
                config.detected += 1
                await config.save()
                await self.log_action(member.guild, f"**{member.guild.get_member(actor) or actor}** added bots.\nThreshold: {config.bot_threshold}")
                await self._punish(member.guild, actor, "Bot spam detected")
                try:
                    await member.ban(reason="Antinuke: Bot spam")
                except discord.Forbidden:
                    pass

    @commands.group(name="antinuke", aliases=["an"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx: Context):
        """Antinuke commands."""
        await ctx.send_help(ctx.command)

    @antinuke.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def an_enable(self, ctx: Context):
        """Enable antinuke."""
        config = await self.get_config(ctx.guild.id)
        config.enabled = True
        await config.save()
        await ctx.success("Antinuke enabled.")

    @antinuke.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def an_disable(self, ctx: Context):
        """Disable antinuke."""
        config = await self.get_config(ctx.guild.id)
        config.enabled = False
        await config.save()
        await ctx.success("Antinuke disabled.")

    @antinuke.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def an_setup(self, ctx: Context):
        """Interactive antinuke setup."""
        view = AntinukeSetupView(ctx)
        embed = discord.Embed(
            title="Antinuke Setup",
            description="Configure your anti-nuke settings using the buttons below.",
            color=ctx.bot.color,
        )
        await ctx.send(embed=embed, view=view)

    @antinuke.command(name="log")
    @commands.has_permissions(administrator=True)
    async def an_log(self, ctx: Context, channel: discord.TextChannel):
        """Set the antinuke log channel."""
        config = await self.get_config(ctx.guild.id)
        config.log_channel_id = channel.id
        await config.save()
        await ctx.success(f"Antinuke log channel set to {channel.mention}")

    @antinuke.command(name="whitelist")
    @commands.has_permissions(administrator=True)
    async def an_whitelist(self, ctx: Context, user: discord.Member):
        """Whitelist/blacklist a user."""
        config = await self.get_config(ctx.guild.id)
        whitelist = config.whitelist or []
        if user.id in whitelist:
            whitelist.remove(user.id)
            await ctx.success(f"Removed {user.mention} from whitelist.")
        else:
            whitelist.append(user.id)
            await ctx.success(f"Added {user.mention} to whitelist.")
        config.whitelist = whitelist
        await config.save()

    @antinuke.command(name="punishment")
    @commands.has_permissions(administrator=True)
    async def an_punishment(self, ctx: Context, punishment: str):
        """Set punishment: ban/kick/none."""
        if punishment.lower() not in ("ban", "kick", "none"):
            return await ctx.error("Punishment must be `ban`, `kick`, or `none`.")
        config = await self.get_config(ctx.guild.id)
        config.punishment = punishment.lower()
        await config.save()
        await ctx.success(f"Punishment set to `{punishment.lower()}`.")

    @antinuke.command(name="config")
    @commands.has_permissions(administrator=True)
    async def an_config(self, ctx: Context):
        """View current antinuke config."""
        config = await self.get_config(ctx.guild.id)
        whitelist = [self.bot.get_user(uid) for uid in (config.whitelist or [])]
        embed = self.bot.embed(ctx, title="Antinuke Config")
        embed.add_field(name="Status", value="Enabled" if config.enabled else "Disabled", inline=True)
        embed.add_field(name="Punishment", value=config.punishment, inline=True)
        embed.add_field(name="Detected", value=str(config.detected), inline=True)
        embed.add_field(name="Actioned", value=str(config.actioned), inline=True)
        embed.add_field(name="Anti Channel", value=str(config.anti_channel), inline=True)
        embed.add_field(name="Anti Role", value=str(config.anti_role), inline=True)
        embed.add_field(name="Anti Ban", value=str(config.anti_ban), inline=True)
        embed.add_field(name="Anti Kick", value=str(config.anti_kick), inline=True)
        embed.add_field(name="Anti Webhook", value=str(config.anti_webhook), inline=True)
        embed.add_field(name="Anti Bot", value=str(config.anti_bot), inline=True)
        embed.add_field(name="Channel Threshold", value=str(config.channel_threshold), inline=True)
        embed.add_field(name="Role Threshold", value=str(config.role_threshold), inline=True)
        embed.add_field(name="Ban Threshold", value=str(config.ban_threshold), inline=True)
        embed.add_field(name="Kick Threshold", value=str(config.kick_threshold), inline=True)
        embed.add_field(name="Webhook Threshold", value=str(config.webhook_threshold), inline=True)
        embed.add_field(name="Bot Threshold", value=str(config.bot_threshold), inline=True)
        embed.add_field(name="Whitelist", value=", ".join(str(u) for u in whitelist if u) or "None", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntinukeCog(bot))
