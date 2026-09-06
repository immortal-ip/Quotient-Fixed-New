from tortoise import fields

from models import BaseDbModel


class VoiceChannel(BaseDbModel):
    class Meta:
        table = "voice_channels"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField(index=True, unique=True)
    owner_id = fields.BigIntField(index=True)
    name = fields.CharField(max_length=100)
    user_limit = fields.IntField(default=0)
    is_locked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now=True)
