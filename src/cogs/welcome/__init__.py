from __future__ import annotations

import io
import random
from typing import Optional

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import Welcome


class WelcomeSetupView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=180)
        self.ctx = ctx
        self.welcome: Optional[Welcome] = None

    async def get_welcome(self):
        self.welcome, _ = await Welcome.get_or_create(guild_id=self.ctx.guild.id)

    @discord.ui.button(label="Channel", style=discord.ButtonStyle.blurple)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the channel where you want welcome messages. Mention it or send the channel ID.",
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

        self.welcome.channel_id = channel.id
        await self.welcome.save()
        await interaction.edit_original_response(content=f"Welcome channel set to {channel.mention}")

    @discord.ui.button(label="Title", style=discord.ButtonStyle.blurple)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the welcome embed title.\nAvailable variables: `{user}`, `{server}`, `{member_count}`",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        self.welcome.title = msg.content
        await self.welcome.save()
        await interaction.edit_original_response(content=f"Welcome title updated to: {msg.content}")

    @discord.ui.button(label="Description", style=discord.ButtonStyle.blurple)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the welcome embed description.\nAvailable variables: `{user}`, `{server}`, `{member_count}`",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        self.welcome.description = msg.content
        await self.welcome.save()
        await interaction.edit_original_response(content=f"Welcome description updated.")

    @discord.ui.button(label="Image", style=discord.ButtonStyle.blurple)
    async def set_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the welcome image URL. Send `none` to remove the image.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        if msg.content.lower() in ("none", "remove", "delete"):
            self.welcome.image_url = None
        else:
            self.welcome.image_url = msg.content.strip()

        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome image updated.")

    @discord.ui.button(label="Thumbnail", style=discord.ButtonStyle.blurple)
    async def set_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the welcome thumbnail URL. Send `none` to remove.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        if msg.content.lower() in ("none", "remove", "delete"):
            self.welcome.thumbnail_url = None
        else:
            self.welcome.thumbnail_url = msg.content.strip()

        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome thumbnail updated.")

    @discord.ui.button(label="Color", style=discord.ButtonStyle.blurple)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send a hex color code (e.g., `#FF0000`).",
            ephemeral=True,
        )

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

        self.welcome.color = color
        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome embed color updated.")

    @discord.ui.button(label="Footer", style=discord.ButtonStyle.blurple)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message("Send the welcome footer text.", ephemeral=True)

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        self.welcome.footer_text = msg.content
        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome footer updated.")

    @discord.ui.button(label="Bot Msg", style=discord.ButtonStyle.blurple)
    async def set_bot_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        await interaction.response.send_message(
            "Send the welcome message for bots.\nAvailable variables: `{user}`, `{server}`, `{member_count}`",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg: discord.Message = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        self.welcome.bot_message = msg.content
        await self.welcome.save()
        await interaction.edit_original_response(content="Bot welcome message updated.")

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.green)
    async def enable_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        if not self.welcome.channel_id:
            return await interaction.edit_original_response(content="Set a channel first before enabling welcome messages.")
        self.welcome.enabled = True
        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome messages are now **enabled**.")

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.red)
    async def disable_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        self.welcome.enabled = False
        await self.welcome.save()
        await interaction.edit_original_response(content="Welcome messages are now **disabled**.")

    @discord.ui.button(label="Preview", style=discord.ButtonStyle.grey)
    async def preview_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.get_welcome()
        if not self.welcome.channel_id:
            return await interaction.edit_original_response(content="No channel set. Please set a channel first.")
        self.welcome.enabled = True
        await self.welcome.save()
        channel = self.ctx.guild.get_channel(self.welcome.channel_id)
        if channel is None:
            return await interaction.edit_original_response(content="Welcome channel not found.")
        await self.send_welcome(channel, self.ctx.author, is_bot=False)
        await interaction.edit_original_response(content=f"Preview sent to {channel.mention}")


class WelcomeCog(Cog, name="Welcome"):
    def __init__(self, bot):
        self.bot = bot

    def _replace_vars(self, text: str, member: discord.Member, guild: discord.Guild) -> str:
        return (
            text.replace("{user}", member.mention)
            .replace("{username}", member.display_name)
            .replace("{server}", guild.name)
            .replace("{member_count}", str(guild.member_count))
        )

    async def send_welcome(self, channel: discord.TextChannel, member: discord.Member, is_bot: bool):
        welcome = await Welcome.get_or_none(guild_id=channel.guild.id)
        if not welcome or not welcome.enabled or welcome.channel_id != channel.id:
            return

        if is_bot and welcome.bot_message:
            text = self._replace_vars(welcome.bot_message, member, channel.guild)
            await channel.send(text)
            return

        if welcome.message_type == "text":
            text = self._replace_vars(welcome.description or "", member, channel.guild)
            await channel.send(text)
            return

        embed = discord.Embed(
            title=self._replace_vars(welcome.title, member, channel.guild),
            description=self._replace_vars(welcome.description, member, channel.guild),
            color=welcome.color or 65459,
        )
        if welcome.image_url:
            embed.set_image(url=welcome.image_url)
        if welcome.thumbnail_url:
            embed.set_thumbnail(url=welcome.thumbnail_url)
        if welcome.footer_text:
            embed.set_footer(text=welcome.footer_text)

        await channel.send(embed=embed)

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome = await Welcome.get_or_none(guild_id=member.guild.id)
        if not welcome or not welcome.enabled or not welcome.channel_id:
            return
        channel = member.guild.get_channel(welcome.channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return
        await self.send_welcome(channel, member, is_bot=member.bot)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def wsetup(self, ctx: Context):
        """Setup welcome messages with interactive buttons."""
        view = WelcomeSetupView(ctx)
        embed = discord.Embed(
            title="Welcome Setup",
            description="Use the buttons below to configure your welcome messages.\n\n"
                        "**Variables:** `{user}`, `{username}`, `{server}`, `{member_count}`",
            color=ctx.bot.color,
        )
        embed.add_field(name="Channel", value="Set the channel for welcome messages", inline=False)
        embed.add_field(name="Title", value="Set the embed title", inline=False)
        embed.add_field(name="Description", value="Set the embed description", inline=False)
        embed.add_field(name="Image", value="Set the welcome image URL", inline=False)
        embed.add_field(name="Thumbnail", value="Set the welcome thumbnail URL", inline=False)
        embed.add_field(name="Color", value="Set the embed color (hex)", inline=False)
        embed.add_field(name="Footer", value="Set the embed footer", inline=False)
        embed.add_field(name="Bot Msg", value="Set a different message for bots", inline=False)
        embed.add_field(name="Enable/Disable", value="Toggle welcome messages", inline=False)
        embed.add_field(name="Preview", value="Test your welcome message", inline=False)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def wdisable(self, ctx: Context):
        """Disable welcome messages."""
        welcome, _ = await Welcome.get_or_create(guild_id=ctx.guild.id)
        welcome.enabled = False
        await welcome.save()
        await ctx.success("Welcome messages have been **disabled**.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def wenable(self, ctx: Context):
        """Enable welcome messages."""
        welcome, _ = await Welcome.get_or_create(guild_id=ctx.guild.id)
        if not welcome.channel_id:
            return await ctx.error("Please set a welcome channel first using `+wsetup`.")
        welcome.enabled = True
        await welcome.save()
        await ctx.success("Welcome messages have been **enabled**.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx: Context):
        """Test your welcome message."""
        welcome = await Welcome.get_or_none(guild_id=ctx.guild.id)
        if not welcome or not welcome.channel_id:
            return await ctx.error("No welcome message configured. Use `+wsetup` to set one up.")
        channel = ctx.guild.get_channel(welcome.channel_id)
        if channel is None:
            return await ctx.error("Welcome channel not found. Please set a valid channel.")
        await self.send_welcome(channel, ctx.author, is_bot=False)
        await ctx.success(f"Welcome message sent to {channel.mention}")


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
