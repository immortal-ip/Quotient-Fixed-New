from __future__ import annotations

from tortoise import fields

from models import BaseDbModel


class VcConfig(BaseDbModel):
    class Meta:
        table = "vc_config"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField(index=True, unique=True)
    role_id = fields.BigIntField(null=True)
    muted_role_id = fields.BigIntField(null=True)
