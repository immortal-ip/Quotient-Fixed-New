from __future__ import annotations

from typing import Optional

from tortoise import fields

from models import BaseDbModel


class Antinuke(BaseDbModel):
    class Meta:
        table = "antinuke"

    guild_id = fields.BigIntField(pk=True, index=True)
    enabled = fields.BooleanField(default=False)
    log_channel_id = fields.BigIntField(null=True)
    whitelist = fields.JSONField(default=list)
    punishment = fields.CharField(default="ban", max_length=20)
    anti_channel = fields.BooleanField(default=True)
    anti_role = fields.BooleanField(default=True)
    anti_ban = fields.BooleanField(default=True)
    anti_kick = fields.BooleanField(default=True)
    anti_webhook = fields.BooleanField(default=True)
    anti_bot = fields.BooleanField(default=True)
    anti_perms = fields.BooleanField(default=True)
    anti_emoji = fields.BooleanField(default=True)
    anti_sticker = fields.BooleanField(default=True)
    anti_invite = fields.BooleanField(default=True)
    channel_threshold = fields.IntField(default=3)
    role_threshold = fields.IntField(default=3)
    ban_threshold = fields.IntField(default=2)
    kick_threshold = fields.IntField(default=3)
    webhook_threshold = fields.IntField(default=2)
    bot_threshold = fields.IntField(default=1)
    perms_threshold = fields.IntField(default=3)
    emoji_threshold = fields.IntField(default=3)
    sticker_threshold = fields.IntField(default=3)
    invite_threshold = fields.IntField(default=5)
    detected = fields.IntField(default=0)
    actioned = fields.IntField(default=0)
