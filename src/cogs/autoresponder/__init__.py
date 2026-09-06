from __future__ import annotations

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import Autoresponder


class ARSetupView(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=180)
        self.ctx = ctx

    @discord.ui.button(label="Add AR", style=discord.ButtonStyle.blurple)
    async def add_ar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Send the trigger word/phrase for this autoresponder.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            trigger_msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        trigger = trigger_msg.content.strip()

        await interaction.edit_original_response(content="Send the response for this trigger.")
        try:
            response_msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        response = response_msg.content.strip()
        embed_bool = await self.ctx.prompt("Do you want this response to be an embed? (yes/no)")

        if embed_bool:
            await interaction.edit_original_response(content="Send the embed title.")
            try:
                title_msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
            except TimeoutError:
                return await interaction.edit_original_response(content="Timed out.")
            embed_title = title_msg.content.strip()

            await interaction.edit_original_response(content="Send the embed description.")
            try:
                desc_msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
            except TimeoutError:
                return await interaction.edit_original_response(content="Timed out.")
            embed_description = desc_msg.content.strip()

            await interaction.edit_original_response(content="Send a hex color code for the embed (e.g., #FF0000). Send `none` for default.")
            try:
                color_msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
            except TimeoutError:
                return await interaction.edit_original_response(content="Timed out.")

            color = 65459
            color_str = color_msg.content.strip().lstrip("#")
            if color_str.lower() not in ("none", "default"):
                try:
                    color = int(color_str, 16)
                except ValueError:
                    return await interaction.edit_original_response(content="Invalid color. Using default color.")

            await Autoresponder.create(
                guild_id=self.ctx.guild.id,
                trigger=trigger,
                response=response,
                is_embed=True,
                embed_title=embed_title,
                embed_description=embed_description,
                embed_color=color,
            )
        else:
            await Autoresponder.create(
                guild_id=self.ctx.guild.id,
                trigger=trigger,
                response=response,
                is_embed=False,
            )

        await interaction.edit_original_response(content=f"Autoresponder added for trigger: `{trigger}`")

    @discord.ui.button(label="List AR", style=discord.ButtonStyle.green)
    async def list_ar(self, interaction: discord.Interaction, button: discord.ui.Button):
        records = await Autoresponder.filter(guild_id=self.ctx.guild.id)
        if not records:
            return await interaction.edit_original_response(content="No autoresponders set.")

        lines = []
        for idx, rec in enumerate(records, start=1):
            status = "✅" if rec.enabled else "❌"
            lines.append(f"`{idx:02}` {status} **{rec.trigger}** → {rec.response[:50]}")

        await interaction.edit_original_response(content="\n".join(lines))

    @discord.ui.button(label="Remove AR", style=discord.ButtonStyle.red)
    async def remove_ar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Send the trigger word/phrase you want to remove.",
            ephemeral=True,
        )

        def check(m: discord.Message):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            msg = await self.ctx.bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return await interaction.edit_original_response(content="Timed out.")

        trigger = msg.content.strip()
        record = await Autoresponder.get_or_none(guild_id=self.ctx.guild.id, trigger=trigger)
        if not record:
            return await interaction.edit_original_response(content="No autoresponder found with that trigger.")

        await record.delete()
        await interaction.edit_original_response(content=f"Removed autoresponder for trigger: `{trigger}`")


class AutoresponderCog(Cog, name="Autoresponder"):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        records = await Autoresponder.filter(guild_id=message.guild.id, enabled=True)
        for rec in records:
            if rec.trigger.lower() in message.content.lower():
                if rec.is_embed:
                    embed = discord.Embed(
                        title=rec.embed_title,
                        description=rec.embed_description,
                        color=rec.embed_color or 65459,
                    )
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send(rec.response)
                break

    @commands.group(invoke_without_command=True)
    async def ar(self, ctx: Context):
        """Autoresponder commands."""
        await ctx.send_help(ctx.command)

    @ar.command(name="panel")
    async def ar_panel(self, ctx: Context):
        """Open the interactive autoresponder control panel."""
        view = ARSetupView(ctx)
        embed = discord.Embed(
            title="Autoresponder Control Panel",
            description="Use the buttons below to manage autoresponders.",
            color=ctx.bot.color,
        )
        await ctx.send(embed=embed, view=view)

    @ar.command(name="add")
    async def ar_add(self, ctx: Context):
        """Add a new autoresponder rule."""
        await ctx.send("Use `&ar panel` to add autoresponders interactively, or use the panel buttons.")

    @ar.command(name="remove")
    async def ar_remove(self, ctx: Context):
        """Remove an autoresponder rule."""
        await ctx.send("Use `&ar panel` to remove autoresponders interactively, or use the panel buttons.")

    @ar.command(name="list")
    async def ar_list(self, ctx: Context):
        """List all autoresponders."""
        records = await Autoresponder.filter(guild_id=ctx.guild.id)
        if not records:
            return await ctx.error("No autoresponders set.")

        lines = []
        for idx, rec in enumerate(records, start=1):
            status = "✅" if rec.enabled else "❌"
            lines.append(f"`{idx:02}` {status} **{rec.trigger}** → {rec.response[:50]}")

        await ctx.send("\n".join(lines))


async def setup(bot):
    await bot.add_cog(AutoresponderCog(bot))
