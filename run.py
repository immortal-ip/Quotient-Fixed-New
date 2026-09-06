import sys
import os
import subprocess
import asyncio

root = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(root, "src")

if root not in sys.path:
    sys.path.insert(0, root)
if src not in sys.path:
    sys.path.insert(0, src)

os.chdir(root)

try:
    import config
except ImportError:
    print("Error: config.py not found in project root.")
    sys.exit(1)

# Auto-install requirements
req_file = os.path.join(root, "requirements.txt")
if os.path.exists(req_file):
    print("[Setup] Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"])
else:
    print("[Setup] requirements.txt not found, skipping pip install.")

# Set DATABASE_URL for migrations from config.POSTGRESQL
if getattr(config, "POSTGRESQL", None):
    os.environ.setdefault("DATABASE_URL", config.POSTGRESQL)

async def run_migrations():
    sys.path.insert(0, root)
    try:
        from migrate_antinuke import migrate as migrate_antinuke_fn
        print("[Migration] Running antinuke migration...")
        await migrate_antinuke_fn()
    except Exception as e:
        print(f"[Migration] Antinuke migration failed: {e}")

    try:
        from migrate_ticket import migrate as migrate_ticket_fn
        print("[Migration] Running ticket migration...")
        await migrate_ticket_fn()
    except Exception as e:
        print(f"[Migration] Ticket migration failed: {e}")

print("[Migration] Running database migrations...")
asyncio.run(run_migrations())

from core import bot

bot.run(bot.config.DISCORD_TOKEN)
