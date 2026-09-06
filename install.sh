#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────────────────────
#  Quotient Bot - Termux Installation Script
#  Run once: bash install.sh
# ─────────────────────────────────────────────────────────────

set -e

echo "==> Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "==> Installing system dependencies..."
pkg install -y python python-pip postgresql libpq openssl-tool git

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Setting up PostgreSQL..."
pg_ctl -D $PREFIX/var/lib/postgresql initdb 2>/dev/null || true
pg_ctl -D $PREFIX/var/lib/postgresql start 2>/dev/null || true
sleep 2

echo "==> Creating database and user..."
psql -U $(whoami) -c "CREATE USER quotient WITH PASSWORD 'quotient123';" postgres 2>/dev/null || true
psql -U $(whoami) -c "CREATE DATABASE quotient OWNER quotient;" postgres 2>/dev/null || true

echo ""
echo "==> Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to src/.env"
echo "     cp .env.example src/.env"
echo ""
echo "  2. Edit src/.env and fill in your DISCORD_TOKEN"
echo "     nano src/.env"
echo ""
echo "  3. For local PostgreSQL, use:"
echo "     DATABASE_URL=postgresql://quotient:quotient123@localhost:5432/quotient"
echo ""
echo "  4. Start the bot:"
echo "     bash start.sh"
