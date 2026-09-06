from __future__ import annotations

from difflib import get_close_matches
from typing import List, Mapping

import discord
from discord.ext import commands
from discord.ui import Select, View

import config
from models import Guild
from utils import LinkButton, LinkType, QuoPaginator, discord_timestamp, truncate_string

from .Cog import Cog


CATEGORY_MAP = {
    "Esports": ["Esports", "ScrimEvents", "SlotManagerEvents", "Ssverification", "TagEvents", "TourneyEvents", "SlashCog"],
    "Moderation": ["Mod", "RoleEvents", "LockEvents"],
    "Utility": ["utility", "quomisc", "QuoAlerts"],
    "Ticket": ["Ticket"],
    "Voice": ["Voice"],
    "Music": ["Music"],
    "Fun": ["Fun"],
    "Welcome": ["Welcome"],
    "Autoresponder": ["Autoresponder"],
    "Role Management": ["Role Management"],
    "Antinuke": ["Antinuke"],
}

EMOJI_MAP = {
    "Esports": "🏆",
    "Moderation": "🛡️",
    "Utility": "🔧",
    "Ticket": "🎫",
    "Voice": "🎙️",
    "Music": "🎵",
    "Fun": "🎉",
    "Welcome": "👋",
    "Autoresponder": "💬",
    "Role Management": "👑",
    "Antinuke": "🛡️",
}

SUPPORT_LINK = "https://discord.gg/ztWygxkX8k"
INVITE_LINK = "https://discord.com/oauth2/authorize?client_id=1389464536314286120&permissions=8&integration_type=0&scope=bot"


class HelpSelect(Select):
    def __init__(self, mapping: Mapping[Cog, List[commands.Command]], help_cmd: "HelpCommand"):
        options = []
        for category in CATEGORY_MAP:
            options.append(
                discord.SelectOption(
                    label=category,
                    emoji=EMOJI_MAP.get(category, "📁"),
                    value=category,
                )
            )

        if not options:
            options.append(
                discord.SelectOption(
                    label="No categories available",
                    description="There are no cogs to display",
                    emoji="⚠️",
                    value="none",
                )
            )

        super().__init__(
            placeholder="Select a category to view commands...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        self.mapping = mapping
        self.help_cmd = help_cmd

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "none":
            return await interaction.response.defer()

        category_cogs = CATEGORY_MAP.get(value, [])
        cogs_in_category = [c for c in self.mapping if c and c.qualified_name in category_cogs]

        embed = discord.Embed(color=0x2C2F33)
        embed.title = f"{EMOJI_MAP.get(value, '📁')} {value} Commands"

        lines = []
        for cog in cogs_in_category:
            cmds = list(self.mapping[cog])
            filtered = await self.help_cmd.filter_commands(cmds, sort=True)
            if not filtered:
                continue

            lines.append(f"**__{cog.qualified_name.title()}__**")
            for cmd in filtered:
                lines.append(f"┃ `{cmd.qualified_name}` — {truncate_string(cmd.short_doc or 'No description', 55)}")
            lines.append("")

        embed.description = "\n".join(lines).strip() or "No commands available in this category."

        prefix = self.help_cmd.context.prefix
        embed.set_footer(text=f"Use {prefix}help <command> for more info")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HomeButton(discord.ui.Button):
    def __init__(self, help_cmd: "HelpCommand"):
        super().__init__(style=discord.ButtonStyle.secondary, emoji="🏠", label="Home", row=2)
        self.help_cmd = help_cmd

    async def callback(self, interaction: discord.Interaction):
        ctx = self.help_cmd.context
        mapping = self.help_cmd.get_bot_mapping()

        embed = discord.Embed(color=0x2C2F33)
        embed.set_thumbnail(url=getattr(ctx.guild.me.display_avatar, "url", ctx.me.display_avatar.url))

        desc = "**Help Menu**\n"
        desc += "Select a category from the dropdown below to view commands.\n"
        desc += "Use `help <command>` for detailed command info.\n\n"

        desc += "**Categories**\n"
        for category in CATEGORY_MAP:
            emoji = EMOJI_MAP.get(category, "📁")
            desc += f"{emoji} **{category}**\n"

        embed.description = desc

        view = HelpView(mapping, self.help_cmd)
        await interaction.response.edit_message(embed=embed, view=view)


class SupportButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.link, emoji="💬", label="Support", url=SUPPORT_LINK, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class InviteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.link, emoji="➕", label="Invite", url=INVITE_LINK, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class HelpView(View):
    def __init__(self, mapping: Mapping[Cog, List[commands.Command]], help_cmd: "HelpCommand"):
        super().__init__(timeout=300)
        self.add_item(HelpSelect(mapping, help_cmd))
        self.add_item(SupportButton())
        self.add_item(InviteButton())
        self.add_item(HomeButton(help_cmd))


class HelpCommand(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__(
            verify_checks=False,
            command_attrs={
                "cooldown": commands.CooldownMapping.from_cooldown(1, 8.0, commands.BucketType.member),
                "help": "Shows help about the bot, a command, or a category",
            },
        )

    @property
    def color(self):
        return self.context.bot.color

    async def send_bot_help(self, mapping: Mapping[Cog, List[commands.Command]]):
        ctx = self.context

        embed = discord.Embed(color=0x2C2F33)
        embed.set_thumbnail(url=getattr(ctx.guild.me.display_avatar, "url", ctx.me.display_avatar.url))

        desc = "**Help Menu**\n"
        desc += "Select a category from the dropdown below to view commands.\n"
        desc += "Use `help <command>` for detailed command info.\n\n"

        desc += "**Categories**\n"
        for category in CATEGORY_MAP:
            emoji = EMOJI_MAP.get(category, "📁")
            desc += f"{emoji} **{category}**\n"

        embed.description = desc

        view = HelpView(mapping, self)
        await ctx.send(embed=embed, embed_perms=True, view=view)

    async def send_group_help(self, group: commands.Group):
        prefix = self.context.prefix

        if not group.commands:
            return await self.send_command_help(group)

        embed = discord.Embed(color=discord.Color(self.color))

        embed.title = f"{group.qualified_name} {group.signature}"
        _help = group.help or "No description provided..."

        _cmds = "\n".join(f"`{prefix}{c.qualified_name}` : {truncate_string(c.short_doc,60)}" for c in group.commands)

        embed.description = f"> {_help}\n\n**Subcommands**\n{_cmds}"

        embed.set_footer(text=f'Use "{prefix}help <command>" for more information.')

        if group.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{aliases}`" for aliases in group.aliases),
                inline=False,
            )

        examples = []
        if group.extras:
            if _gif := group.extras.get("gif"):
                embed.set_image(url=_gif)

            if _ex := group.extras.get("examples"):
                examples = [f"{self.context.prefix}{i}" for i in _ex]

        if examples:
            examples: str = "\n".join(examples)  # type: ignore
            embed.add_field(name="Examples", value=f"```{examples}```")

        await self.context.send(embed=embed, embed_perms=True)

    async def send_cog_help(self, cog: Cog):
        paginator = QuoPaginator(self.context, per_page=14)
        c = 0
        for cmd in cog.get_commands():
            if not cmd.hidden:
                _brief = "No Information..." if not cmd.short_doc else truncate_string(cmd.short_doc, 60)
                paginator.add_line(f"`{cmd.qualified_name}` : {_brief}")
                c += 1

        paginator.title = f"{cog.qualified_name.title()} ({c})"
        await paginator.start()

    async def send_command_help(self, cmd: commands.Command):
        embed = discord.Embed(color=self.color)
        embed.title = "Command: " + cmd.qualified_name

        examples = []

        alias = ",".join((f"`{alias}`" for alias in cmd.aliases)) if cmd.aliases else "No aliases"
        _text = (
            f"**Description:** {cmd.help or 'No help found...'}\n"
            f"**Usage:** `{self.get_command_signature(cmd)}`\n"
            f"**Aliases:** {alias}\n"
            f"**Examples:**"
        )

        if cmd.extras:
            if _gif := cmd.extras.get("gif"):
                embed.set_image(url=_gif)

            if _ex := cmd.extras.get("examples"):
                examples = [f"{self.context.prefix}{i}" for i in _ex]

        examples: str = "\n".join(examples) if examples else "Command has no examples"  # type: ignore

        _text += f"```{examples}```"

        embed.description = _text

        await self.context.send(embed=embed, embed_perms=True)

    async def command_not_found(self, string: str):
        message = f"Could not find the `{string}` command. "
        commands_list = (str(cmd) for cmd in self.context.bot.walk_commands())

        if dym := "\n".join(get_close_matches(string, commands_list)):
            message += f"Did you mean...\n{dym}"

        return message
