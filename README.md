# Quo x - The Ultimate Discord Bot for Esports Management

![Python](https://img.shields.io/badge/python-3.11-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.0-blue)
![Database](https://img.shields.io/badge/db-PostgreSQL-blue)
![ORM](https://img.shields.io/badge/orm-Tortoise_ORM-purple)

> The source here is only for educational purposes.

Quo x is the ultimate open-source Discord bot designed specifically for esports servers. Our goal is to empower esports communities by simplifying and streamlining the organization and management of scrims, tournaments, and other events.

---

## Features

Quo x is a multi-functional bot that provides a comprehensive range of features, including:

- Automated Scrims Management
- Automated Tournaments Management
- Easy to use Web-Dashboard
- Community engagement tools
- Premium / Payments Integration
- Anti-Nuke Protection
- Auto Moderation
- Music Player
- Ticket System
- Custom Tags & Reminders
- and much much more...

---

## Installation

### Prerequisites

- **Python 3.11+**
- **PostgreSQL** database (Supabase recommended)
- **Discord Bot Token** ([Discord Developer Portal](https://discord.com/developers/applications))

### 1. Clone the repository

```bash
git clone https://github.com/quotientbot/Quotient-Bot.git
cd Quotient-Bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the bot

Edit `config.py` and fill in the required values:

```python
# Discord Bot Token
DISCORD_TOKEN = "YOUR_BOT_TOKEN"

# PostgreSQL Connection String
POSTGRESQL = "postgres://user:password@host:port/database"

# Tortoise ORM Config
TORTOISE = {
    'connections': {
        'default': 'postgres://user:password@host:port/database'
    },
    'apps': {
        'models': {
            'models': [
                'models.misc',
                'models.esports',
                'models.helpers',
            ],
            'default_connection': 'default',
        }
    }
}

# Extensions / Cogs
EXTENSIONS = (
    'cogs.antinuke',
    'cogs.autoresponder',
    'cogs.esports',
    'cogs.events',
    'cogs.fun',
    'cogs.mod',
    'cogs.music',
    'cogs.premium',
    'cogs.quomisc',
    'cogs.reminder',
    'cogs.role',
    'server',
    'cogs.ticket',
    'cogs.utility',
    'cogs.voice',
    'cogs.welcome',
)

# Server Port for Web Dashboard
SERVER_PORT = 8080
```

---

## Running the Bot

### Option A: Local / VSCode

```bash
py run.py
```

#### Run in VSCode

Press **F5** or use the pre-configured launch configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Quo x Bot",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run.py",
      "console": "integratedTerminal"
    }
  ]
}
```

### Option B: Hosting (VPS / Dedicated / Cloud)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the bot (auto-runs migrations on first start)
py run.py
```

#### Run with PM2 (Recommended for 24/7 hosting)

```bash
pm2 start run.py --name quotient-bot --interpreter python
pm2 save
pm2 startup
```

#### Run with systemd

Create `/etc/systemd/system/quotient-bot.service`:

```ini
[Unit]
Description=Quo x Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/Quotient-Bot
ExecStart=/usr/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable quotient-bot
sudo systemctl start quotient-bot
```

---

## Database Migrations

The bot automatically runs migrations on startup via `run.py`. If you need to run migrations manually:

```bash
# Antinuke table migration
py migrate_antinuke.py

# Ticket table migration
py migrate_ticket.py
```

---

## Commands & Categories

| Category | Description |
|----------|-------------|
| **Esports** | Scrims, Tournaments, Slot Manager, Tag Checks, SS Verification |
| **Mod** | Moderation tools, cleanup, lockdown, warnings |
| **Premium** | Premium plans, payments, perks |
| **Antinuke** | Anti-raid, anti-channel-create, anti-role, anti-ban, anti-bot |
| **Ticket** | Support ticket system |
| **Music** | Play music in voice channels |
| **Utility** | Embed builder, polls, reminders |
| **Fun** | Fun commands |
| **Role** | Reaction roles, role menus |
| **Welcome** | Welcome messages, autoroles |
| **Autoresponder** | Auto replies to triggers |
| **Events** | Giveaways, join/leave logs |

---

## Environment Variables (Optional)

For hosting platforms like Heroku, Railway, or Render, you can use environment variables instead of editing `config.py`:

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Your Discord bot token |
| `DATABASE_URL` | PostgreSQL connection string |
| `SERVER_PORT` | Port for web dashboard (default: 8080) |
| `PREFIX` | Bot prefix (default: `q`) |

---

## Tech Stack

- **Language:** Python 3.11
- **Bot Framework:** discord.py 2.3.0
- **Database:** PostgreSQL (via asyncpg)
- **ORM:** Tortoise ORM
- **Web Framework:** FastAPI + aiohttp
- **Real-time:** python-socketio

---

## Contributing

Contributions are Welcome:) kindly open an issue first for discussion.

It's also a good option to join the [Support Server](https://discord.gg/ztWygxkX8k)

---

## Contact Us

If you have any questions or feedback, please feel free to reach out DM me on dc **{alone.ogg}** or create an issue on this repository. Thank you for choosing Quo x!

---

## Fixed & Maintained By

- **alone.ogg** — Bug fixes, dependency resolution, hosting setup, code stabilization, and README.

---

## License

This project is licensed under the MPL-2.0 license - see the [LICENSE](LICENSE) file for details.

