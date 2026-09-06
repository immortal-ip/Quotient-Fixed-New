from tortoise import fields

from models import BaseDbModel


class TicketTranscript(BaseDbModel):
    class Meta:
        table = "ticket_transcripts"

    id = fields.IntField(pk=True)
    ticket_id = fields.BigIntField(index=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField(index=True)
    user_id = fields.BigIntField(index=True)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now=True)


class TicketLog(BaseDbModel):
    class Meta:
        table = "ticket_logs"

    id = fields.IntField(pk=True)
    ticket_id = fields.BigIntField(index=True)
    guild_id = fields.BigIntField(index=True)
    action = fields.CharField(max_length=100)
    user_id = fields.BigIntField(index=True)
    moderator_id = fields.BigIntField(null=True)
    reason = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now=True)


class TicketConfig(BaseDbModel):
    class Meta:
        table = "ticket_config"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField(index=True, unique=True)
    category_id = fields.BigIntField(null=True)
    log_channel_id = fields.BigIntField(null=True)
    staff_role_id = fields.BigIntField(null=True)
    support_role_id = fields.BigIntField(null=True)
    ticket_count = fields.IntField(default=0)
    transcript_channel_id = fields.BigIntField(null=True)
    panel_channel_id = fields.BigIntField(null=True)
    panel_title = fields.TextField(null=True)
    panel_description = fields.TextField(null=True)
    panel_color = fields.IntField(null=True)
    panel_image_url = fields.TextField(null=True)
