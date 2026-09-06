from __future__ import annotations

from tortoise import fields

from models import BaseDbModel


class RoleAlias(BaseDbModel):
    class Meta:
        table = "role_aliases"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    role_id = fields.BigIntField(index=True)
    alias = fields.CharField(max_length=100, index=True)
