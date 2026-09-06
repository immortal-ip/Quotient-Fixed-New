from __future__ import annotations

import io
import random

import aiohttp
import discord
from discord.ext import commands

from core import Cog, Context

GIPHY_API_KEY = "RwQaiIyVSW99gKU1nwrXMZNDYn77WNhX"
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

ACTIONS = [
    "kiss", "hug", "lick", "pat", "slap", "cuddle", "waifu", "bully", "nom",
    "wave", "smile", "bonk", "blush", "wink", "yeet", "highfive", "handhold", "bite", "glomp",
]


class FunCommands(Cog, name="Fun"):
    def __init__(self, bot):
        self.bot = bot

    async def _fetch_gif(self, action: str) -> str | None:
        params = {
            "api_key": GIPHY_API_KEY,
            "q": action,
            "limit": 20,
            "rating": "pg-13",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(GIPHY_SEARCH_URL, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    results = data.get("data", [])
                    if results:
                        return random.choice(results)["images"]["original"]["url"]
        except Exception:
            pass
        return None

    async def _download_bytes(self, url: str) -> bytes | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception:
            pass
        return None

    async def _send_action(self, ctx: Context, action: str, member: discord.Member | None = None):
        action = action.lower()
        gif_url = await self._fetch_gif(action)
        if not gif_url:
            return await ctx.send(f"Could not fetch a {action} GIF right now. Try again later.")

        target = member or ctx.author
        if ctx.author.id == target.id:
            content = f"**{ctx.author.display_name}** {action}s themselves"
        else:
            content = f"**{ctx.author.display_name}** {action}s {target.mention}"

        gif_bytes = await self._download_bytes(gif_url)
        embed = discord.Embed(title=f"{action.capitalize()}!", color=discord.Color.blurple())

        if gif_bytes:
            file = discord.File(io.BytesIO(gif_bytes), filename=f"{action}.gif")
            embed.set_image(url=f"attachment://{action}.gif")
            await ctx.send(content=content, embed=embed, file=file)
        else:
            embed.set_image(url=gif_url)
            await ctx.send(content=content, embed=embed)

    @commands.command()
    async def kiss(self, ctx: Context, member: discord.Member = None):
        """Kiss someone."""
        await self._send_action(ctx, "kiss", member)

    @commands.command()
    async def hug(self, ctx: Context, member: discord.Member = None):
        """Hug someone."""
        await self._send_action(ctx, "hug", member)

    @commands.command()
    async def pat(self, ctx: Context, member: discord.Member = None):
        """Pat someone."""
        await self._send_action(ctx, "pat", member)

    @commands.command()
    async def slap(self, ctx: Context, member: discord.Member = None):
        """Slap someone."""
        await self._send_action(ctx, "slap", member)

    @commands.command()
    async def cuddle(self, ctx: Context, member: discord.Member = None):
        """Cuddle someone."""
        await self._send_action(ctx, "cuddle", member)

    @commands.command()
    async def lick(self, ctx: Context, member: discord.Member = None):
        """Lick someone."""
        await self._send_action(ctx, "lick", member)

    @commands.command()
    async def waifu(self, ctx: Context, member: discord.Member = None):
        """Waifu someone."""
        await self._send_action(ctx, "waifu", member)

    @commands.command()
    async def bully(self, ctx: Context, member: discord.Member = None):
        """Bully someone."""
        await self._send_action(ctx, "bully", member)

    @commands.command()
    async def nom(self, ctx: Context, member: discord.Member = None):
        """Nom someone."""
        await self._send_action(ctx, "nom", member)

    @commands.command()
    async def wave(self, ctx: Context, member: discord.Member = None):
        """Wave at someone."""
        await self._send_action(ctx, "wave", member)

    @commands.command()
    async def smile(self, ctx: Context, member: discord.Member = None):
        """Smile at someone."""
        await self._send_action(ctx, "smile", member)

    @commands.command()
    async def bonk(self, ctx: Context, member: discord.Member = None):
        """Bonk someone."""
        await self._send_action(ctx, "bonk", member)

    @commands.command()
    async def blush(self, ctx: Context, member: discord.Member = None):
        """Blush at someone."""
        await self._send_action(ctx, "blush", member)

    @commands.command()
    async def wink(self, ctx: Context, member: discord.Member = None):
        """Wink at someone."""
        await self._send_action(ctx, "wink", member)

    @commands.command()
    async def yeet(self, ctx: Context, member: discord.Member = None):
        """Yeet someone."""
        await self._send_action(ctx, "yeet", member)

    @commands.command()
    async def highfive(self, ctx: Context, member: discord.Member = None):
        """High five someone."""
        await self._send_action(ctx, "highfive", member)

    @commands.command()
    async def handhold(self, ctx: Context, member: discord.Member = None):
        """Hold someone's hand."""
        await self._send_action(ctx, "handhold", member)

    @commands.command()
    async def bite(self, ctx: Context, member: discord.Member = None):
        """Bite someone."""
        await self._send_action(ctx, "bite", member)

    @commands.command()
    async def glomp(self, ctx: Context, member: discord.Member = None):
        """Glomp someone."""
        await self._send_action(ctx, "glomp", member)

    @commands.command()
    async def gif(self, ctx: Context, action: str, member: discord.Member = None):
        """Send a random action GIF. Usage: gif <action> [@user]"""
        await self._send_action(ctx, action, member)

    @commands.command()
    async def gif_test(self, ctx: Context):
        """Test GIF embed."""
        await self._send_action(ctx, "kiss", None)


async def setup(bot):
    await bot.add_cog(FunCommands(bot))
