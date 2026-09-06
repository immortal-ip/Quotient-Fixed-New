from __future__ import annotations

import io
from datetime import datetime

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import TicketConfig, TicketLog, TicketTranscript
from utils import emote


class TicketSetupView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=180)
        self.ctx = ctx

    async def get_config(self):
        config, _ = await TicketConfig.get_or_create(guild_id=self.ctx.guild.id)
        return config

    @discord.ui.button(label="Panel Channel", style=discord.ButtonStyle.blurple)
    async def set_panel_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message(
            "Send the channel where you want the ticket panel to be sent. Mention it or send the channel ID.",
            ephemeral=True,
        )

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
            return await interaction.edit_original_response(content="Invalid channel. Please mention a text channel or send a valid channel ID.")

        config.panel_channel_id = channel.id
        await config.save()
        await interaction.edit_original_response(content=f"Ticket panel channel set to {channel.mention}")

    @discord.ui.button(label="Category", style=discord.ButtonStyle.blurple)
    async def set_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message(
            "Send the ticket category channel ID or mention the category.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        category = None
        if msg.channel_mentions:
            category = msg.channel_mentions[0]
        else:
            try:
                category = self.ctx.guild.get_channel(int(msg.content.strip()))
            except ValueError:
                pass

        if category is None or not isinstance(category, discord.CategoryChannel):
            return await interaction.edit_original_response(content="Invalid category. Please mention a category or send a valid category ID.")

        config.category_id = category.id
        await config.save()
        await interaction.edit_original_response(content=f"Ticket category set to {category.mention}")

    @discord.ui.button(label="Staff Role", style=discord.ButtonStyle.blurple)
    async def set_staff_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message(
            "Send the staff role mention or role ID.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        role = None
        if msg.role_mentions:
            role = msg.role_mentions[0]
        else:
            try:
                role = self.ctx.guild.get_role(int(msg.content.strip()))
            except ValueError:
                pass

        if role is None:
            return await interaction.edit_original_response(content="Invalid role. Please mention a role or send a valid role ID.")

        config.staff_role_id = role.id
        await config.save()
        await interaction.edit_original_response(content=f"Staff role set to {role.mention}")

    @discord.ui.button(label="Log Channel", style=discord.ButtonStyle.blurple)
    async def set_log_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message(
            "Send the ticket log channel. Mention it or send the channel ID.",
            ephemeral=True,
        )

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

    @discord.ui.button(label="Transcript Channel", style=discord.ButtonStyle.blurple)
    async def set_transcript_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message(
            "Send the transcript channel. Mention it or send the channel ID.",
            ephemeral=True,
        )

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

        config.transcript_channel_id = channel.id
        await config.save()
        await interaction.edit_original_response(content=f"Transcript channel set to {channel.mention}")

    @discord.ui.button(label="Panel Title", style=discord.ButtonStyle.blurple)
    async def set_panel_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send the panel embed title.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        config.panel_title = msg.content
        await config.save()
        await interaction.edit_original_response(content=f"Panel title updated to: {msg.content}")

    @discord.ui.button(label="Panel Description", style=discord.ButtonStyle.blurple)
    async def set_panel_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send the panel embed description.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        config.panel_description = msg.content
        await config.save()
        await interaction.edit_original_response(content="Panel description updated.")

    @discord.ui.button(label="Panel Color", style=discord.ButtonStyle.blurple)
    async def set_panel_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send a hex color code (e.g., `#FF0000`).", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        color_str = msg.content.strip().lstrip("#")
        try:
            color = int(color_str, 16)
        except ValueError:
            return await interaction.edit_original_response(content="Invalid color code. Send a hex like `#FF0000`.")

        config.panel_color = color
        await config.save()
        await interaction.edit_original_response(content="Panel color updated.")

    @discord.ui.button(label="Panel Image", style=discord.ButtonStyle.blurple)
    async def set_panel_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        await interaction.response.send_message("Send the panel image URL. Send `none` to remove.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        if msg.content.lower() in ("none", "remove", "delete"):
            config.panel_image_url = None
        else:
            config.panel_image_url = msg.content.strip()

        await config.save()
        await interaction.edit_original_response(content="Panel image updated.")

    @discord.ui.button(label="Send Panel", style=discord.ButtonStyle.green)
    async def send_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = await self.get_config()
        if not config.panel_channel_id:
            return await interaction.edit_original_response(content="Set a panel channel first.")

        channel = self.ctx.guild.get_channel(config.panel_channel_id)
        if channel is None:
            return await interaction.edit_original_response(content="Panel channel not found.")

        embed = discord.Embed(
            title=config.panel_title or "🎫 Ticket System",
            description=config.panel_description or "Need help? Create a ticket below!",
            color=config.panel_color or 0x3498DB,
        )
        if config.panel_image_url:
            embed.set_image(url=config.panel_image_url)

        view = TicketControlsView()
        await channel.send(embed=embed, view=view)
        await interaction.edit_original_response(content=f"Panel sent to {channel.mention}")


class TicketControlsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        config = await TicketConfig.get_or_none(guild_id=interaction.guild_id)
        if not config or not config.category_id:
            return await interaction.followup.send("Tickets are not configured for this server.", ephemeral=True)

        category = interaction.guild.get_channel(config.category_id)
        if not category:
            return await interaction.followup.send("Ticket category not found. Contact an admin.", ephemeral=True)

        existing = discord.utils.get(category.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            return await interaction.followup.send(f"You already have an open ticket: {existing.mention}", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }

        if config.staff_role_id:
            staff_role = interaction.guild.get_role(config.staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}",
        )

        config.ticket_count += 1
        await config.save()

        embed = discord.Embed(
            title=f"Ticket #{config.ticket_count}",
            description=f"**User:** {interaction.user.mention}\nPlease wait for staff to assist you.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Ticket ID: {channel.id}")

        view = TicketManageView(channel)
        staff_mention = f"<@&{config.staff_role_id}>" if config.staff_role_id else ""
        await channel.send(content=staff_mention, embed=embed, view=view)

        await TicketLog.create(
            ticket_id=channel.id,
            guild_id=interaction.guild_id,
            action="created",
            user_id=interaction.user.id,
            reason="",
        )

        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)


class TicketManageView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.Button):
        config = await TicketConfig.get_or_none(guild_id=interaction.guild_id)
        if not config or not config.staff_role_id:
            return await interaction.response.send_message("Staff role not configured.", ephemeral=True)

        staff_role = interaction.guild.get_role(config.staff_role_id)
        if not staff_role or staff_role not in interaction.user.roles:
            return await interaction.response.send_message("Only staff can claim tickets.", ephemeral=True)

        embed = interaction.message.embed
        embed.set_author(name=f"Claimed by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.message.edit(embed=embed, view=None)
        await self.channel.send(f"🎫 Ticket claimed by {interaction.user.mention}")

        await TicketLog.create(
            ticket_id=self.channel.id,
            guild_id=interaction.guild_id,
            action="claimed",
            user_id=self.channel.id,
            moderator_id=interaction.user.id,
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.Button):
        view = ConfirmCloseView(self.channel)
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=view, ephemeral=True)

    @discord.ui.button(label="Add User", style=discord.ButtonStyle.blurple, emoji="➕", custom_id="ticket_add_user")
    async def add_user(self, interaction: discord.Interaction, button: discord.Button):
        config = await TicketConfig.get_or_none(guild_id=interaction.guild_id)
        if not config or not config.staff_role_id:
            return await interaction.response.send_message("Staff role not configured.", ephemeral=True)

        staff_role = interaction.guild.get_role(config.staff_role_id)
        if not staff_role or staff_role not in interaction.user.roles:
            return await interaction.response.send_message("Only staff can add users.", ephemeral=True)

        modal = discord.ui.Modal(title="Add User to Ticket")
        user_id = discord.ui.TextInput(label="User ID", placeholder="Enter user ID to add")
        modal.add_item(user_id)

        async def on_submit(modal_interaction: discord.Interaction):
            try:
                user_id = int(user_id.value.strip())
                user = interaction.guild.get_member(user_id)
                if not user:
                    return await modal_interaction.response.send_message("User not found.", ephemeral=True)
                await self.channel.set_permissions(user, read_messages=True, send_messages=True, read_message_history=True)
                await modal_interaction.response.send_message(f"{user.mention} has been added to the ticket.", ephemeral=True)
            except ValueError:
                await modal_interaction.response.send_message("Invalid user ID.", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove User", style=discord.ButtonStyle.red, emoji="➖", custom_id="ticket_remove_user")
    async def remove_user(self, interaction: discord.Interaction, button: discord.Button):
        config = await TicketConfig.get_or_none(guild_id=interaction.guild_id)
        if not config or not config.staff_role_id:
            return await interaction.response.send_message("Staff role not configured.", ephemeral=True)

        staff_role = interaction.guild.get_role(config.staff_role_id)
        if not staff_role or staff_role not in interaction.user.roles:
            return await interaction.response.send_message("Only staff can remove users.", ephemeral=True)

        modal = discord.ui.Modal(title="Remove User from Ticket")
        user_id = discord.ui.TextInput(label="User ID", placeholder="Enter user ID to remove")
        modal.add_item(user_id)

        async def on_submit(modal_interaction: discord.Interaction):
            try:
                user_id = int(user_id.value.strip())
                user = interaction.guild.get_member(user_id)
                if not user:
                    return await modal_interaction.response.send_message("User not found.", ephemeral=True)
                await self.channel.set_permissions(user, overwrite=None)
                await modal_interaction.response.send_message(f"{user.mention} has been removed from the ticket.", ephemeral=True)
            except ValueError:
                await modal_interaction.response.send_message("Invalid user ID.", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.grey, emoji="✏️", custom_id="ticket_rename")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.Button):
        config = await TicketConfig.get_or_none(guild_id=interaction.guild_id)
        if not config or not config.staff_role_id:
            return await interaction.response.send_message("Staff role not configured.", ephemeral=True)

        staff_role = interaction.guild.get_role(config.staff_role_id)
        if not staff_role or staff_role not in interaction.user.roles:
            return await interaction.response.send_message("Only staff can rename tickets.", ephemeral=True)

        modal = discord.ui.Modal(title="Rename Ticket")
        new_name = discord.ui.TextInput(label="New Name", placeholder="ticket-username")
        modal.add_item(new_name)

        async def on_submit(modal_interaction: discord.Interaction):
            new_name = new_name.value.strip().lower().replace(" ", "-")
            if not new_name.startswith("ticket-"):
                new_name = f"ticket-{new_name}"
            await self.channel.edit(name=new_name)
            await modal_interaction.response.send_message(f"Ticket renamed to {self.channel.name}", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


class ConfirmCloseView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=30)
        self.channel = channel

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.channel.send("🔒 Ticket is being closed. Transcript is being generated...")

        messages = []
        async for msg in self.channel.history(limit=None, oldest_first=True):
            messages.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}")
            for att in msg.attachments:
                messages.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: [Attachment: {att.url}]")

        ticket_name = self.channel.name.replace("ticket-", "")
        try:
            ticket_user_id = int(ticket_name)
        except ValueError:
            ticket_user_id = 0

        transcript = "\n".join(messages)
        await TicketTranscript.create(
            ticket_id=self.channel.id,
            guild_id=self.channel.guild.id,
            channel_id=self.channel.id,
            user_id=ticket_user_id,
            content=transcript,
        )

        config = await TicketConfig.get_or_none(guild_id=self.channel.guild.id)
        if config and config.transcript_channel_id:
            transcript_channel = self.channel.guild.get_channel(config.transcript_channel_id)
            if transcript_channel:
                file = discord.File(io.StringIO(transcript), filename=f"transcript-{self.channel.id}.txt")
                embed = discord.Embed(title=f"Transcript - {self.channel.name}", color=discord.Color.blue())
                await transcript_channel.send(embed=embed, file=file)

        await TicketLog.create(
            ticket_id=self.channel.id,
            guild_id=self.channel.guild.id,
            action="closed",
            user_id=ticket_user_id,
            moderator_id=interaction.user.id,
        )

        await self.channel.delete()

    @discord.ui.button(label="No", style=discord.ButtonStyle.grey)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Ticket close cancelled.", view=None)


class TicketCog(Cog, name="Ticket"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def tsetup(self, ctx: Context):
        """Setup ticket system with interactive buttons."""
        config, _ = await TicketConfig.get_or_create(guild_id=ctx.guild.id)

        if not config.category_id:
            category = await ctx.guild.create_category("Tickets")
            config.category_id = category.id
            await config.save()

        if not config.log_channel_id:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
            log_channel = await ctx.guild.create_text_channel("ticket-logs", overwrites=overwrites)
            config.log_channel_id = log_channel.id
            await config.save()

        if not config.staff_role_id:
            staff_role = await ctx.guild.create_role(name="Staff")
            config.staff_role_id = staff_role.id
            await config.save()

        if not config.transcript_channel_id:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
            transcript_channel = await ctx.guild.create_text_channel("ticket-transcripts", overwrites=overwrites)
            config.transcript_channel_id = transcript_channel.id
            await config.save()

        view = TicketSetupView(ctx)
        embed = discord.Embed(
            title="🎫 Ticket Setup",
            description="Use the buttons below to configure the ticket system.",
            color=ctx.bot.color,
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(name="tpanel_send")
    @commands.has_permissions(administrator=True)
    async def tpanel_send(self, ctx: Context):
        """Send the ticket panel to the configured channel."""
        config = await TicketConfig.get_or_none(guild_id=ctx.guild.id)
        if not config or not config.panel_channel_id:
            return await ctx.error("Panel channel not configured. Use `+tsetup` first.")

        channel = ctx.guild.get_channel(config.panel_channel_id)
        if channel is None:
            return await ctx.error("Panel channel not found.")

        embed = discord.Embed(
            title=config.panel_title or "🎫 Ticket System",
            description=config.panel_description or "Need help? Create a ticket below!",
            color=config.panel_color or 0x3498DB,
        )
        if config.panel_image_url:
            embed.set_image(url=config.panel_image_url)

        view = TicketControlsView()
        await channel.send(embed=embed, view=view)
        await ctx.success(f"Panel sent to {channel.mention}")

    @commands.command()
    async def tclose(self, ctx: Context):
        """Close the current ticket."""
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.error("This command can only be used in a ticket channel.")
        view = ConfirmCloseView(ctx.channel)
        await ctx.send("Are you sure you want to close this ticket?", view=view)


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
