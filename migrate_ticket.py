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
            ALTER TABLE ticket_config ADD COLUMN IF NOT EXISTS panel_channel_id BIGINT NULL
        """)
        await conn.execute("""
            ALTER TABLE ticket_config ADD COLUMN IF NOT EXISTS panel_title TEXT NULL
        """)
        await conn.execute("""
            ALTER TABLE ticket_config ADD COLUMN IF NOT EXISTS panel_description TEXT NULL
        """)
        await conn.execute("""
            ALTER TABLE ticket_config ADD COLUMN IF NOT EXISTS panel_color INTEGER NULL
        """)
        await conn.execute("""
            ALTER TABLE ticket_config ADD COLUMN IF NOT EXISTS panel_image_url TEXT NULL
        """)
        print("Migration completed successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
