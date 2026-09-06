from __future__ import annotations

from typing import Optional

from tortoise import fields

from models import BaseDbModel


class Autoresponder(BaseDbModel):
    class Meta:
        table = "autoresponders"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    trigger = fields.CharField(max_length=200)
    response = fields.TextField()
    is_embed = fields.BooleanField(default=False)
    embed_title = fields.TextField(null=True)
    embed_description = fields.TextField(null=True)
    embed_color = fields.IntField(null=True)
    enabled = fields.BooleanField(default=True)
