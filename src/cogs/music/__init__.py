from __future__ import annotations

import math

import discord
import wavelink
from discord.ext import commands

from core import Cog, Context
from utils import emote


class PlayerControls(discord.ui.View):
    def __init__(self, player: wavelink.Player, cog: "MusicCommands"):
        super().__init__(timeout=None)
        self.player = player
        self.cog = cog

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔀", label="Shuffle", row=0)
    async def shuffle(self, interaction: discord.Interaction, button: discord.Button):
        if not self.player.queue:
            return await interaction.response.send_message("Queue is empty.", ephemeral=True)
        import random
        queue = list(self.player.queue)
        random.shuffle(queue)
        self.player.queue.clear()
        for track in queue:
            self.player.queue.put(track)
        await interaction.response.send_message("🔀 Queue shuffled.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⏮️", label="Previous", disabled=True, row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message("No previous track history.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="⏸️", label="Pause", row=0)
    async def pause(self, interaction: discord.Interaction, button: discord.Button):
        if not self.player.playing:
            return await interaction.response.send_message("Nothing is playing.", ephemeral=True)
        await self.player.pause(True)
        button.emoji = "▶️"
        button.label = "Resume"
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="▶️", label="Resume", disabled=True, row=0)
    async def resume(self, interaction: discord.Interaction, button: discord.Button):
        if not self.player.paused:
            return await interaction.response.send_message("Nothing is paused.", ephemeral=True)
        await self.player.pause(False)
        button.emoji = "⏸️"
        button.label = "Pause"
        button.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=self)

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji="⏹️", label="Stop", row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.Button):
        self.player.queue.clear()
        await self.player.stop()
        self.cog.autoplay_channels.discard(interaction.channel.id)
        await interaction.response.edit_message(content="Stopped the music.", embed=None, view=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏭️", label="Skip", row=1)
    async def skip(self, interaction: discord.Interaction, button: discord.Button):
        if not self.player.playing:
            return await interaction.response.send_message("Nothing is playing.", ephemeral=True)
        await self.player.stop()
        await interaction.response.send_message("⏭️ Skipped the current song.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔁", label="Loop", row=1)
    async def loop(self, interaction: discord.Interaction, button: discord.Button):
        player = self.player
        if not player.playing:
            return await interaction.response.send_message("Nothing is playing.", ephemeral=True)
        current = getattr(player, "loop", None)
        if current == wavelink.LoopMode.track:
            player.loop = wavelink.LoopMode.off
            await interaction.response.send_message("Loop disabled.", ephemeral=True)
        elif current == wavelink.LoopMode.queue:
            player.loop = wavelink.LoopMode.off
            await interaction.response.send_message("Loop disabled.", ephemeral=True)
        else:
            player.loop = wavelink.LoopMode.track
            await interaction.response.send_message("🔁 Looping current track.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔉", label="Vol-", row=2)
    async def volume_down(self, interaction: discord.Interaction, button: discord.Button):
        player = self.player
        new_vol = max(0, int(player.volume) - 10)
        await player.set_volume(new_vol)
        await interaction.response.send_message(f"Volume set to {new_vol}%", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔊", label="Vol+", row=2)
    async def volume_up(self, interaction: discord.Interaction, button: discord.Button):
        player = self.player
        new_vol = min(1000, int(player.volume) + 10)
        await player.set_volume(new_vol)
        await interaction.response.send_message(f"Volume set to {new_vol}%", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔊", label="Vol+", row=2)
    async def volume_up(self, interaction: discord.Interaction, button: discord.Button):
        player = self.player
        new_vol = min(1000, int(player.volume) + 10)
        await player.set_volume(new_vol)
        await interaction.response.send_message(f"Volume set to {new_vol}%", ephemeral=True)


class MusicCommands(Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.autoplay_channels = set()
        self.player_views = {}
        self._node_connecting = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure_node()

    async def _ensure_node(self):
        if self._node_connecting:
            return
        self._node_connecting = True
        try:
            node = wavelink.Node(
                uri="http://darli.hidencloud.com:24670",
                password="yadavji",
            )
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
        finally:
            self._node_connecting = False

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEvent):
        player: wavelink.Player = payload.player
        if player.channel and player.channel.id in self.autoplay_channels:
            if len(player.channel.members) == 1:
                await player.stop()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEvent):
        player: wavelink.Player = payload.player
        if player.channel and player.channel.id in self.autoplay_channels:
            members = [m for m in player.channel.members if not m.bot]
            if len(members) <= 1 and len(player.queue) == 0:
                await player.stop()

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEvent):
        player: wavelink.Player = payload.player
        if player.playing:
            await player.stop()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEvent):
        print(f"Music node connected: {payload.node}")

    def _progress_bar(self, position: float, duration: float, length: int = 20) -> str:
        if duration <= 0:
            return "▬" * length
        progress = position / duration
        filled = math.floor(progress * length)
        empty = length - filled
        return "▬" * filled + " " * empty

    def _format_time(self, ms: int) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    async def _send_player_card(self, ctx: Context, player: wavelink.Player):
        track = player.current
        if not track:
            return

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = "🎵 NOW PLAYING"
        embed.description = (
            f"**{track.title}**\n"
            f"{track.author}\n\n"
            f"👤 Requested by {ctx.author.display_name}"
        )

        artwork = getattr(track, "artwork", None) or getattr(track, "thumbnail", None) or ctx.me.display_avatar.url
        embed.set_thumbnail(url=artwork)

        position = int(getattr(player, "position", 0) or 0)
        duration = int(getattr(track, "length", 0) or 0)
        bar = self._progress_bar(position, duration)
        embed.add_field(
            name="Progress",
            value=f"{self._format_time(position)} ▬━━━━━━━━━━━━━━━━ {self._format_time(duration)}",
            inline=False,
        )

        queue_len = len(player.queue)
        embed.add_field(
            name="Volume",
            value=f"🔊 {int(player.volume)}%",
            inline=True,
        )
        embed.add_field(
            name="Queue",
            value=f"📋 {queue_len}",
            inline=True,
        )

        embed.set_footer(text=f"Channel Owner: {ctx.author.display_name}")

        view = PlayerControls(player, self)
        self.player_views[player.channel.id] = view
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def join(self, ctx: Context):
        """Join your voice channel."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        await self._ensure_node()

        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        elif player.channel != ctx.author.voice.channel:
            await player.move_to(ctx.author.voice.channel)

        await ctx.send(f"Joined {ctx.author.voice.channel.mention}")

    @commands.command()
    async def disconnect(self, ctx: Context):
        """Disconnect from voice channel."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            return await ctx.send("Not connected to any voice channel.")

        await player.disconnect()
        self.autoplay_channels.discard(ctx.channel.id)
        self.player_views.pop(ctx.channel.id, None)
        await ctx.send("Disconnected from voice channel.")

    @commands.command()
    async def nodeinfo(self, ctx: Context):
        """Check Lavalink node status."""
        await self._ensure_node()
        nodes = wavelink.Pool.nodes
        if not nodes:
            return await ctx.send("No Lavalink nodes connected.")

        info = []
        for node in nodes.values():
            info.append(f"Node: {node}\nConnected: {getattr(node, 'connected', 'unknown')}")

        await ctx.send("\n\n".join(info))

    @commands.command()
    async def play(self, ctx: Context, *, query: str):
        """Play a song from URL or search query."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        await self._ensure_node()

        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        elif player.channel != ctx.author.voice.channel:
            await player.move_to(ctx.author.voice.channel)

        if query.startswith(("http://", "https://")):
            search_query = query
        else:
            search_query = f"ytsearch:{query}"

        try:
            tracks = await wavelink.Pool.fetch_tracks(search_query)
        except Exception as e:
            return await ctx.send(f"Search failed: {e}")

        if not tracks:
            return await ctx.send(
                "No tracks found.\n"
                "Try:\n"
                "1. Using a direct YouTube URL\n"
                "2. Checking if your Lavalink server has YouTube search enabled\n"
                "3. Using a different Lavalink server"
            )

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                player.queue.put(track)
            await ctx.send(f"Added playlist **{tracks.name}** with {len(tracks.tracks)} tracks to queue.")
        else:
            track = tracks[0]
            player.queue.put(track)
            await ctx.send(f"Added to queue: **{track.title}**")

        if not player.playing:
            await player.play(player.queue.get())
            await self._send_player_card(ctx, player)

    @commands.command()
    async def search(self, ctx: Context, *, query: str):
        """Search for songs."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        await self._ensure_node()

        search_query = f"ytsearch:{query}" if not query.startswith(("http://", "https://")) else query

        try:
            tracks = await wavelink.Pool.fetch_tracks(search_query)
        except Exception as e:
            return await ctx.send(f"Could not find any tracks matching that query. Error: {e}")

        if not tracks:
            return await ctx.send("No tracks found. Try a different search term or check if the Lavalink server has YouTube search enabled.")

        embed = discord.Embed(title="Search Results", color=discord.Color.blue())
        for i, track in enumerate(tracks[:10], 1):
            duration = int(getattr(track, "length", 0) or 0)
            embed.add_field(
                name=f"{i}. {track.title}",
                value=f"Duration: {duration // 60000}:{(duration % 60000) // 1000:02d}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx: Context):
        """Pause the current song."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send("Nothing is playing.")

        await player.pause(True)
        await ctx.send("Paused the current song.")

    @commands.command()
    async def resume(self, ctx: Context):
        """Resume the paused song."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not getattr(player, "paused", False):
            return await ctx.send("Nothing is paused.")

        await player.pause(False)
        await ctx.send("Resumed the song.")

    @commands.command()
    async def skip(self, ctx: Context):
        """Skip the current song."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send("Nothing is playing.")

        await player.stop()
        await ctx.send("Skipped the current song.")

    @commands.command()
    async def stop(self, ctx: Context):
        """Stop the music and clear the queue."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send("Nothing is playing.")

        player.queue.clear()
        await player.stop()
        await ctx.send("Stopped the music and cleared the queue.")

    @commands.command()
    async def seek(self, ctx: Context, position: str):
        """Seek to a position in the song (e.g., 1:30 or 90)."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send("Nothing is playing.")

        try:
            if ":" in position:
                minutes, seconds = position.split(":")
                seek_pos = int(minutes) * 60 + int(seconds)
            else:
                seek_pos = int(position)
        except ValueError:
            return await ctx.send("Invalid position format. Use `1:30` or `90`.")

        await player.seek(seek_pos * 1000)
        await ctx.send(f"Seeked to {position}")

    @commands.command()
    async def autoplay(self, ctx: Context, mode: str = None):
        """Toggle autoplay mode (on/off)."""
        player: wavelink.Player = ctx.guild.voice_client
        if not mode:
            status = "enabled" if ctx.channel.id in self.autoplay_channels else "disabled"
            return await ctx.send(f"Autoplay is currently {status} for this channel.")

        if mode.lower() in ("on", "enable", "yes"):
            self.autoplay_channels.add(ctx.channel.id)
            await ctx.send("Autoplay enabled. The bot will keep playing songs even if everyone leaves.")
        elif mode.lower() in ("off", "disable", "no"):
            self.autoplay_channels.discard(ctx.channel.id)
            await ctx.send("Autoplay disabled.")
        else:
            await ctx.send("Usage: `autoplay on` or `autoplay off`")

    @commands.command(name="247")
    async def twofourseven(self, ctx: Context, mode: str = None):
        """Toggle 24/7 mode for the voice channel."""
        player: wavelink.Player = ctx.guild.voice_client
        if not mode:
            status = "enabled" if ctx.channel.id in self.autoplay_channels else "disabled"
            return await ctx.send(f"24/7 mode is currently {status} for this channel.")

        if mode.lower() in ("on", "enable", "yes"):
            self.autoplay_channels.add(ctx.channel.id)
            await ctx.send("24/7 mode enabled. The bot will stay in the voice channel and keep playing.")
        elif mode.lower() in ("off", "disable", "no"):
            self.autoplay_channels.discard(ctx.channel.id)
            await ctx.send("24/7 mode disabled.")
        else:
            await ctx.send("Usage: `247 on` or `247 off`")

    @commands.command()
    async def volume(self, ctx: Context, volume: int):
        """Set the volume (0-1000)."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            return await ctx.send("Not connected to any voice channel.")

        if not 0 <= volume <= 1000:
            return await ctx.send("Volume must be between 0 and 1000.")

        await player.set_volume(volume)
        await ctx.send(f"Volume set to {volume}%")

    @commands.command()
    async def queue(self, ctx: Context):
        """Show the current queue."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or len(player.queue) == 0:
            return await ctx.send("The queue is empty.")

        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
        for i, track in enumerate(list(player.queue)[:10], 1):
            duration = int(getattr(track, "length", 0) or 0)
            embed.add_field(
                name=f"{i}. {track.title}",
                value=f"Duration: {duration // 60000}:{(duration % 60000) // 1000:02d}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def nowplaying(self, ctx: Context):
        """Show the current song."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send("Nothing is playing.")

        await self._send_player_card(ctx, player)

    @commands.command()
    async def loop(self, ctx: Context, mode: str = None):
        """Set loop mode: off, track, queue."""
        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            return await ctx.send("Not connected to any voice channel.")

        if not mode:
            current = getattr(player, "loop", None)
            current = "off" if not current else ("track" if current == wavelink.LoopMode.track else "queue")
            return await ctx.send(f"Current loop mode: {current}")

        if mode.lower() == "off":
            player.loop = wavelink.LoopMode.off
            await ctx.send("Loop disabled.")
        elif mode.lower() == "track":
            player.loop = wavelink.LoopMode.track
            await ctx.send("Looping current track.")
        elif mode.lower() == "queue":
            player.loop = wavelink.LoopMode.queue
            await ctx.send("Looping the queue.")
        else:
            await ctx.send("Usage: `loop off`, `loop track`, or `loop queue`")


async def setup(bot):
    await bot.add_cog(MusicCommands(bot))
