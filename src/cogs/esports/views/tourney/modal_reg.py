from __future__ import annotations
from typing import Dict, Optional, TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from core import Quotient

_pending: Dict = {}


def _key(user_id: int, tourney_id: int) -> tuple:
    return (user_id, tourney_id)


class RegistrationStep1(discord.ui.Modal, title="Registration Form - Step 1"):
    team_name = discord.ui.TextInput(label="Team Name", placeholder="Enter team name", required=True, max_length=50)
    owner_name = discord.ui.TextInput(label="Team Owner's Name", placeholder="Enter owner's name", required=True, max_length=50)
    owner_email = discord.ui.TextInput(label="Team Owner's Email", placeholder="Enter Owner's email", required=True, max_length=100)
    owner_phone = discord.ui.TextInput(label="Team Owner's Phone No.", placeholder="Enter Owner's phone number", required=True, max_length=20)

    def __init__(self, tourney_id: int):
        super().__init__()
        self.tourney_id = tourney_id

    async def on_submit(self, interaction: discord.Interaction):
        _pending[_key(interaction.user.id, self.tourney_id)] = {
            "team_name": self.team_name.value,
            "owner_name": self.owner_name.value,
            "owner_email": self.owner_email.value,
            "owner_phone": self.owner_phone.value,
        }
        v = discord.ui.View(timeout=420)
        v.add_item(ContinueStep2Btn(self.tourney_id))
        await interaction.response.send_message(
            "✅ Step 1 Completed! Proceed below to continue your registration.\n"
            "⏱️ Hurry! You have 7 minutes left to complete your registration.",
            view=v, ephemeral=True,
        )


class RegistrationStep2(discord.ui.Modal, title="Player Details - Step 2"):
    player1 = discord.ui.TextInput(label="Player 1 (UID, IGN)", placeholder="e.g. 1234567890, PlayerName", required=True, max_length=100)
    player2 = discord.ui.TextInput(label="Player 2 (UID, IGN)", placeholder="e.g. 1234567890, PlayerName", required=True, max_length=100)
    player3 = discord.ui.TextInput(label="Player 3 (UID, IGN)", placeholder="e.g. 1234567890, PlayerName", required=True, max_length=100)
    player4 = discord.ui.TextInput(label="Player 4 (UID, IGN)", placeholder="e.g. 1234567890, PlayerName", required=True, max_length=100)

    def __init__(self, tourney_id: int):
        super().__init__()
        self.tourney_id = tourney_id

    async def on_submit(self, interaction: discord.Interaction):
        k = _key(interaction.user.id, self.tourney_id)
        if k not in _pending:
            return await interaction.response.send_message("❌ Session expired. Please start registration again.", ephemeral=True)
        _pending[k].update({
            "player1": self.player1.value,
            "player2": self.player2.value,
            "player3": self.player3.value,
            "player4": self.player4.value,
        })
        v = discord.ui.View(timeout=420)
        v.add_item(ContinueStep3Btn(self.tourney_id))
        await interaction.response.send_message(
            "✅ Step 2 Completed! Click below to continue to the final step.",
            view=v, ephemeral=True,
        )


class RegistrationStep3(discord.ui.Modal, title="Substitutes & Instagram - Step 3"):
    sub1 = discord.ui.TextInput(label="Substitute 1 (UID, IGN)", placeholder="or 'no'", required=True, max_length=100)
    sub2 = discord.ui.TextInput(label="Substitute 2 (UID, IGN)", placeholder="or 'no'", required=True, max_length=100)
    insta_followed = discord.ui.TextInput(label="Followed on Instagram?", placeholder="yes / no", required=True, max_length=10)
    insta_handles = discord.ui.TextInput(label="Player's Insta Handles", placeholder="all registered @player's insta id", required=True, max_length=200, style=discord.TextStyle.paragraph)

    def __init__(self, tourney_id: int, bot: "Quotient"):
        super().__init__()
        self.tourney_id = tourney_id
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        from models import Tourney, TMSlot

        k = _key(interaction.user.id, self.tourney_id)
        if k not in _pending:
            return await interaction.response.send_message("❌ Session expired. Please start registration again.", ephemeral=True)

        data = _pending.pop(k)
        data.update({
            "sub1": self.sub1.value,
            "sub2": self.sub2.value,
            "insta_followed": self.insta_followed.value,
            "insta_handles": self.insta_handles.value,
        })

        await interaction.response.defer(ephemeral=True)

        tourney = await Tourney.get_or_none(pk=self.tourney_id)
        if not tourney:
            return await interaction.followup.send("❌ Tournament not found.", ephemeral=True)
        if not tourney.started_at:
            return await interaction.followup.send("❌ Registrations are currently closed.", ephemeral=True)
        if interaction.user.id in tourney.banned_users:
            return await interaction.followup.send("❌ You are banned from this tournament.", ephemeral=True)

        count = await tourney.assigned_slots.all().count()
        if count >= tourney.total_slots:
            return await interaction.followup.send("❌ All slots are filled!", ephemeral=True)

        already = await tourney.assigned_slots.filter(leader_id=interaction.user.id).exists()
        if already and not tourney.multiregister:
            return await interaction.followup.send("❌ You have already registered for this tournament.", ephemeral=True)

        slot_num = count + tourney.slotlist_start
        slot = await TMSlot.create(
            num=slot_num,
            team_name=data["team_name"],
            leader_id=interaction.user.id,
            members=[interaction.user.id],
            extra_data=data,
        )
        await tourney.assigned_slots.add(slot)

        try:
            if role := tourney.role:
                await interaction.user.add_roles(role, reason="Tourney modal registration")
        except discord.HTTPException:
            pass

        if confirm_ch := tourney.confirm_channel:
            _e = discord.Embed(color=self.bot.color, title="✅ New Registration")
            _e.description = f"**Slot #{slot_num}**"
            _e.add_field(name="Team Name", value=data["team_name"], inline=False)
            _e.add_field(name="Owner", value=data.get("owner_name", "N/A"), inline=True)
            _e.add_field(name="Email", value=data.get("owner_email", "N/A"), inline=True)
            _e.add_field(name="Phone", value=data.get("owner_phone", "N/A"), inline=True)
            players = "\n".join(data.get(f"player{i}", "") for i in range(1, 5) if data.get(f"player{i}"))
            _e.add_field(name="Players", value=players or "N/A", inline=False)
            _e.add_field(name="Substitutes", value=f"{data.get('sub1','N/A')}, {data.get('sub2','N/A')}", inline=True)
            _e.add_field(name="Instagram", value=data.get("insta_handles", "N/A"), inline=False)
            _e.set_footer(text=f"Registered by {interaction.user} ({interaction.user.id})")
            try:
                m = await confirm_ch.send(content=interaction.user.mention, embed=_e, allowed_mentions=discord.AllowedMentions(users=True))
                slot.confirm_jump_url = m.jump_url
                await slot.save()
            except discord.HTTPException:
                pass

        success = tourney.success_message or f"✅ {interaction.user.mention}, your team **{data['team_name']}** has been registered successfully!"
        try:
            if reg_ch := tourney.registration_channel:
                await reg_ch.send(success, allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException:
            pass

        await interaction.followup.send(
            f"🎉 **Registration Complete!**\n"
            f"Your team **{data['team_name']}** has been registered as **Slot #{slot_num}**!\n"
            f"Please tag your teammates in the server.",
            ephemeral=True,
        )


class ContinueStep2Btn(discord.ui.Button):
    def __init__(self, tourney_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, label="▶️ Continue to Step 2")
        self.tourney_id = tourney_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistrationStep2(self.tourney_id))


class ContinueStep3Btn(discord.ui.Button):
    def __init__(self, tourney_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, label="▶️ Continue to Step 3")
        self.tourney_id = tourney_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistrationStep3(self.tourney_id, interaction.client))


class UseOldTeamBtn(discord.ui.Button):
    def __init__(self, tourney_id: int, old_data: dict):
        super().__init__(style=discord.ButtonStyle.green, label="✅ Use Old Team")
        self.tourney_id = tourney_id
        self.old_data = old_data

    async def callback(self, interaction: discord.Interaction):
        from models import Tourney, TMSlot

        await interaction.response.defer(ephemeral=True)
        tourney = await Tourney.get_or_none(pk=self.tourney_id)
        if not tourney or not tourney.started_at:
            return await interaction.followup.send("❌ Registrations are closed.", ephemeral=True)

        count = await tourney.assigned_slots.all().count()
        if count >= tourney.total_slots:
            return await interaction.followup.send("❌ All slots are filled!", ephemeral=True)

        data = self.old_data
        slot_num = count + tourney.slotlist_start
        slot = await TMSlot.create(
            num=slot_num,
            team_name=data.get("team_name", "Unknown"),
            leader_id=interaction.user.id,
            members=[interaction.user.id],
            extra_data=data,
        )
        await tourney.assigned_slots.add(slot)

        try:
            if role := tourney.role:
                await interaction.user.add_roles(role, reason="Tourney re-registration")
        except discord.HTTPException:
            pass

        if confirm_ch := tourney.confirm_channel:
            _e = discord.Embed(color=interaction.client.color, title="✅ Re-Registration (Old Team)")
            _e.description = f"**Slot #{slot_num}**"
            _e.add_field(name="Team Name", value=data.get("team_name", "N/A"), inline=False)
            _e.add_field(name="Owner", value=data.get("owner_name", "N/A"), inline=True)
            _e.add_field(name="Email", value=data.get("owner_email", "N/A"), inline=True)
            _e.add_field(name="Phone", value=data.get("owner_phone", "N/A"), inline=True)
            players = "\n".join(data.get(f"player{i}", "") for i in range(1, 5) if data.get(f"player{i}"))
            _e.add_field(name="Players", value=players or "N/A", inline=False)
            _e.add_field(name="Substitutes", value=f"{data.get('sub1','N/A')}, {data.get('sub2','N/A')}", inline=True)
            _e.add_field(name="Instagram", value=data.get("insta_handles", "N/A"), inline=False)
            _e.set_footer(text=f"Re-registered by {interaction.user} ({interaction.user.id})")
            try:
                m = await confirm_ch.send(content=interaction.user.mention, embed=_e, allowed_mentions=discord.AllowedMentions(users=True))
                slot.confirm_jump_url = m.jump_url
                await slot.save()
            except discord.HTTPException:
                pass

        await interaction.followup.send(
            f"🎉 Re-registered with your old team **{data.get('team_name','Unknown')}** as **Slot #{slot_num}**!",
            ephemeral=True,
        )


class CreateNewTeamBtn(discord.ui.Button):
    def __init__(self, tourney_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, label="🆕 Create New Team")
        self.tourney_id = tourney_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RegistrationStep1(self.tourney_id))


class RegisterTeamBtn(discord.ui.Button):
    def __init__(self, tourney_id: int):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="🎮 Register Team",
            custom_id=f"modal_reg_{tourney_id}",
        )
        self.tourney_id = tourney_id

    async def callback(self, interaction: discord.Interaction):
        from models import Tourney

        tourney = await Tourney.get_or_none(pk=self.tourney_id)
        if not tourney:
            return await interaction.response.send_message("❌ Tournament not found.", ephemeral=True)
        if not tourney.started_at:
            return await interaction.response.send_message("❌ Registrations are currently closed.", ephemeral=True)
        if interaction.user.id in tourney.banned_users:
            return await interaction.response.send_message("❌ You are banned from this tournament.", ephemeral=True)

        prev_slot = await tourney.assigned_slots.filter(leader_id=interaction.user.id).first()

        if prev_slot and not tourney.multiregister:
            old_data = prev_slot.extra_data or {}
            _e = discord.Embed(color=0xFFCC00, title="🧡 Previous Team Found")
            _e.add_field(name="Team Name", value=prev_slot.team_name, inline=False)
            if old_data:
                _e.add_field(name="Owner", value=old_data.get("owner_name", "N/A"), inline=True)
                _e.add_field(name="Email", value=old_data.get("owner_email", "N/A"), inline=True)
                _e.add_field(name="Phone", value=old_data.get("owner_phone", "N/A"), inline=True)
                players = "\n".join(old_data.get(f"player{i}", "") for i in range(1, 5) if old_data.get(f"player{i}"))
                _e.add_field(name="Players", value=players or "N/A", inline=False)
                _e.add_field(name="Substitutes", value=f"{old_data.get('sub1','N/A')}, {old_data.get('sub2','N/A')}", inline=True)
                _e.add_field(name="Instagram", value=old_data.get("insta_handles", "N/A"), inline=False)

            v = discord.ui.View(timeout=60)
            v.add_item(UseOldTeamBtn(self.tourney_id, old_data))
            v.add_item(CreateNewTeamBtn(self.tourney_id))
            return await interaction.response.send_message(
                "💡 You've previously registered. What would you like to do?",
                embed=_e, view=v, ephemeral=True,
            )

        await interaction.response.send_modal(RegistrationStep1(self.tourney_id))


class TourneyRegistrationPanel(discord.ui.View):
    def __init__(self, tourney_id: int):
        super().__init__(timeout=None)
        self.add_item(RegisterTeamBtn(tourney_id))
