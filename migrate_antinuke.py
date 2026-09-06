import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("PYTHONPATH", ".")

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "src", ".env"))
except ImportError:
    pass

from urllib.parse import urlparse, parse_qs

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment variables.")
    sys.exit(1)

import asyncpg

_parsed = urlparse(DATABASE_URL)
_qs = parse_qs(_parsed.query)
_sslmode = _qs.get("sslmode", ["disable"])[0]
_ssl = _sslmode in ("require", "verify-ca", "verify-full")

async def migrate():
    conn = await asyncpg.connect(
        host=_parsed.hostname,
        port=_parsed.port or 5432,
        user=_parsed.username,
        password=_parsed.password,
        database=_parsed.path.lstrip("/"),
        ssl=_ssl,
    )
    try:
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS punishment VARCHAR(20) DEFAULT 'ban'
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_channel BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_role BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_ban BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_kick BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_webhook BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_bot BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_perms BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_emoji BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_sticker BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS anti_invite BOOLEAN DEFAULT TRUE
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS channel_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS role_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS ban_threshold INTEGER DEFAULT 2
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS kick_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS webhook_threshold INTEGER DEFAULT 2
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS bot_threshold INTEGER DEFAULT 1
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS perms_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS emoji_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS sticker_threshold INTEGER DEFAULT 3
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS invite_threshold INTEGER DEFAULT 5
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS detected INTEGER DEFAULT 0
        """)
        await conn.execute("""
            ALTER TABLE antinuke ADD COLUMN IF NOT EXISTS actioned INTEGER DEFAULT 0
        """)
        print("Antinuke migration completed successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
