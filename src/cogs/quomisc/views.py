from __future__ import annotations

import typing

from contextlib import suppress

import discord

from core import Context, QuotientView
from utils import emote


class BaseView(discord.ui.View):
    def __init__(self, ctx: Context, *, timeout=30.0):
        self.ctx = ctx
        self.message: typing.Optional[discord.Message] = None
        self.bot: Quotient = ctx.bot

        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            for b in self.children:
                if isinstance(b, discord.ui.Button) and not b.style == discord.ButtonStyle.link:
                    b.style, b.disabled = discord.ButtonStyle.grey, True

            with suppress(discord.HTTPException):
                if self.message is not None:
                    await self.message.edit(view=self)


class SetupButtonView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="setup scrims", custom_id="setup_scrims_button")
    async def setup_scrims_button(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        return await self.ctx.simple(f"Kindly use `{self.ctx.prefix}sm setup` to setup a scrim.")

    @discord.ui.button(label="setup tourney", custom_id="setup_tourney_button")
    async def setup_tourney_button(self, interaction: discord.Interaction, button: discord.Button):
        return await self.ctx.simple(f"Kindly use `{self.ctx.prefix}t setup` to setup a tournament.")
