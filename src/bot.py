import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    from core import bot

    bot.run(bot.config.DISCORD_TOKEN)
