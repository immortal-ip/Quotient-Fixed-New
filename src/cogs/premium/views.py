from typing import List

import discord

import config
from models import PremiumPlan, PremiumTxn
from utils import emote


class PlanSelector(discord.ui.Select):
    def __init__(self, plans: List[PremiumPlan]):
        super().__init__(placeholder="Select a Quo x Premium Plan... ")

        for _ in plans:
            self.add_option(label=f"{_.name} - ₹{_.price}", description=_.description, value=_.id)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.plan = self.values[0]
        self.view.stop()


class PremiumPurchaseBtn(discord.ui.Button):
    def __init__(self, label="Get Quo x Pro", emoji=emote.diamond, style=discord.ButtonStyle.grey):
        super().__init__(style=style, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        plans = await PremiumPlan.all().order_by("id")
        if not plans:
            return await interaction.followup.send(
                "No premium plans are available at the moment. Please contact the bot owner.",
                ephemeral=True,
            )

        v = discord.ui.View(timeout=100)
        v.plan = None
        v.add_item(PlanSelector(plans))
        await interaction.followup.send("Please select the Quo x Pro plan, you want to opt:", view=v, ephemeral=True)
        await v.wait()

        if not v.plan:
            return

        txn = await PremiumTxn.create(
            txnid=await PremiumTxn.gen_txnid(),
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            plan_id=v.plan,
        )
        _link = config.PAY_LINK + "getpremium" + "?txnId=" + txn.txnid

        await interaction.followup.send(
            f"You are about to purchase Quo x Premium for **{interaction.guild.name}**.\n"
            "If you want to purchase for another server, use `qpremium` or `/premium` command in that server.\n\n"
            f"[*Click Me to Complete the Payment*]({_link})",
            ephemeral=True,
        )


class PremiumView(discord.ui.View):
    def __init__(self, text="This feature requires Quo x Premium.", *, label="Get Quo x Pro"):
        super().__init__(timeout=None)
        self.text = text
        self.add_item(PremiumPurchaseBtn(label=label))

    @property
    def premium_embed(self) -> discord.Embed:
        _e = discord.Embed(
            color=0x00FFB3, description=f"**You discovered a premium feature <a:premium:807911675981201459>**"
        )
        _e.description = (
            f"\n*`{self.text}`*\n\n"
            "__Perks you get with Quo x Pro:__\n"
            f"{emote.check} Access to `Quo x Pro` bot.\n"
            f"{emote.check} Unlimited Scrims.\n"
            f"{emote.check} Unlimited Tournaments.\n"
            f"{emote.check} Custom Reactions for Regs.\n"
            f"{emote.check} Smart SSverification.\n"
            f"{emote.check} Cancel-Claim Panel.\n"
            f"{emote.check} Premium Role + more...\n"
        )
        return _e
