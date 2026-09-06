from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from datetime import datetime, timedelta

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import Commands, Guild
from utils import LinkButton, LinkType, QuoColor, checks, get_ipm, human_timedelta, truncate_string

from .alerts import *
from .dev import *
from .views import SetupButtonView


class Quomisc(Cog, name="quomisc"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command(aliases=("inv",))
    async def invite(self, ctx: Context):
        """Quo x Invite Links."""
        v = discord.ui.View(timeout=None)
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link, label="Invite Quo x (Me)", url=self.bot.config.BOT_INVITE or "https://discord.com", row=1
            )
        )
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link, label="Join Support Server", url=self.bot.config.SERVER_LINK or "https://discord.com", row=2
            )
        )

        await ctx.reply(view=v)

    async def make_private_channel(self, ctx: Context) -> discord.TextChannel:
        support_link = f"[Support Server]({ctx.config.SERVER_LINK})" if ctx.config.SERVER_LINK else ""
        invite_link = f"[Invite Me]({ctx.config.BOT_INVITE})" if ctx.config.BOT_INVITE else ""
        vote_link = f"[Vote]({ctx.config.WEBSITE}/vote)" if ctx.config.WEBSITE else ""

        guild = ctx.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                embed_links=True,
                attach_files=True,
                manage_channels=True,
            ),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }
        channel = await guild.create_text_channel(
            "quox-private", overwrites=overwrites, reason=f"Made by {str(ctx.author)}"
        )
        await Guild.filter(guild_id=ctx.guild.id).update(private_channel=channel.id)

        e = self.bot.embed(ctx)
        e.add_field(
            name="**What is this channel for?**",
            inline=False,
            value="This channel is made for Quo x to send important announcements and activities that need your attention. If anything goes wrong with any of my functionality I will notify you here. Important announcements from the developer will be sent directly here too.\n\nYou can test my commands in this channel if you like. Kindly don't delete it , some of my commands won't work without this channel.",
        )
        links_text = " | ".join(filter(None, [support_link, invite_link, vote_link]))
        e.add_field(
            name="**__Important Links__**", value=links_text or "N/A", inline=False
        )

        links = [LinkType("Support Server", ctx.config.SERVER_LINK)] if ctx.config.SERVER_LINK else []
        view = LinkButton(links) if links else discord.ui.View()
        m = await channel.send(embed=e, view=view)
        await m.pin()

        return channel

    @commands.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True, manage_webhooks=True)
    async def setup_cmd(self, ctx: Context):
        """
        Setup Quo x in the current server.
        This creates a private channel in the server. You can rename that if you like.
        Quo x requires manage channels and manage webhooks permissions for this to work.
        You must have manage server permission.
        """

        _view = SetupButtonView(ctx)
        _view.add_item(QuotientView.tricky_invite_button())
        record = await Guild.get(guild_id=ctx.guild.id)

        if record.private_ch is not None:
            return await ctx.error(f"You already have a private channel ({record.private_ch.mention})", view=_view)
        channel = await self.make_private_channel(ctx)
        await ctx.success(f"Created {channel.mention}", view=_view)

    @commands.command()
    async def ping(self, ctx: Context):
        """Check how the bot is doing"""
        await ctx.send(f"Bot: `{round(self.bot.latency*1000, 2)} ms`, Database: `{await self.bot.db_latency}`")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx: Context, *, new_prefix: str = None):
        """Change your server's prefix"""

        if not new_prefix:
            prefix = self.bot.cache.guild_data[ctx.guild.id].get("prefix", "q")
            return await ctx.simple(f"Prefix for this server is `{prefix}`")

        if len(new_prefix) > 5:
            return await ctx.error(f"Prefix cannot contain more than 5 characters.")

        self.bot.cache.guild_data[ctx.guild.id]["prefix"] = new_prefix
        await Guild.filter(guild_id=ctx.guild.id).update(prefix=new_prefix)
        await ctx.success(f"Updated server prefix to: `{new_prefix}`")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def color(self, ctx: Context, *, new_color: QuoColor):
        """Change color of Quo x's embeds"""
        color = int(str(new_color).replace("#", ""), 16)

        self.bot.cache.guild_data[ctx.guild.id]["color"] = color
        await Guild.filter(guild_id=ctx.guild.id).update(embed_color=color)
        await ctx.success(f"Updated server color.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def footer(self, ctx: Context, *, new_footer: str):
        """Change footer of embeds sent by Quo x"""
        if len(new_footer) > 50:
            return await ctx.success(f"Footer cannot contain more than 50 characters.")

        self.bot.cache.guild_data[ctx.guild.id]["footer"] = new_footer
        await Guild.filter(guild_id=ctx.guild.id).update(embed_footer=new_footer)
        await ctx.send(f"Updated server footer.")


async def setup(bot: Quotient) -> None:
    await bot.add_cog(Quomisc(bot))
    await bot.add_cog(Dev(bot))
    await bot.add_cog(QuoAlerts(bot))
