from __future__ import annotations

from typing import Optional

from tortoise import fields

from models import BaseDbModel


class Welcome(BaseDbModel):
    class Meta:
        table = "welcome"

    guild_id = fields.BigIntField(pk=True, index=True)

    channel_id = fields.BigIntField(null=True)
    enabled = fields.BooleanField(default=False)

    message_type = fields.CharField(default="embed", max_length=10)
    title = fields.TextField(default="Welcome {user}!")
    description = fields.TextField(default="Welcome to **{server}**, {user}!\nYou are our **{member_count}**th member!")
    color = fields.IntField(default=65459)
    image_url = fields.TextField(null=True)
    thumbnail_url = fields.TextField(null=True)
    footer_text = fields.TextField(default="Welcome!")
    bot_message = fields.TextField(default="Welcome bot **{user}** to **{server}**!")
