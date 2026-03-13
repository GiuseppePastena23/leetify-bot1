# Leetify Bot

Telegram bot for tracking CS2 match stats from Leetify.

## Features

- **Automatic Match Reports**: Detects new matches and sends reports to your Telegram group
- **Player Management**: Add, remove, edit, and list tracked players
- **Stats Lookup**: Get detailed stats for any tracked player
- **Player Comparison**: Compare two players side-by-side
- **Leaderboard**: Weekly rankings across multiple metrics
- **Map Breakdown**: See performance per map for players
- **Weekly Digest**: Summary of all matches played during the week

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure the bot**:
   - Edit `.env` with your settings:
     - `TELEGRAM_BOT_TOKEN`: Get from @BotFather
     - `CHAT_ID`: Your group chat ID (forward a message to @userinfobot)
     - `LEETIFY_API_KEY`: Get from https://leetify.com/app/developer
     - `POLLING_INTERVAL`: How often to check for new matches (default: 300 seconds)
     - `WEEKLY_DIGEST_DAY`: Day to send weekly digest (0=Monday, 6=Sunday)
     - `WEEKLY_DIGEST_HOUR`: Hour to send weekly digest (0-23)

3. **Run the bot**:
```bash
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | List all commands |
| `/add <id/url>` | Add player to track |
| `/remove <name>` | Remove player |
| `/edit <old> <new>` | Rename player |
| `/list` | List tracked players |
| `/stats <name>` | Get player stats |
| `/compare <p1> <p2>` | Compare two players |
| `/leaderboard` | Weekly leaderboard |
| `/map [player]` | Map breakdown |
| `/check` | Manually check for new matches |
| `/settings` | View settings |
| `/ping` | Health check |

## Project Structure

```
leetify-bot/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── database.py         # SQLite operations
├── leetify_client.py   # Leetify API wrapper
├── match_detector.py   # Match detection logic
├── weekly_digest.py    # Weekly digest scheduler
├── formatters.py       # Message formatting
├── handlers/          # Telegram command handlers
│   ├── commands.py
│   ├── players.py
│   ├── stats.py
│   └── matches.py
├── .env               # Environment variables
└── requirements.txt   # Dependencies
```

## Running on Raspberry Pi

```bash
# Using screen (recommended)
screen -S leetify-bot
python bot.py
# Detach: Ctrl+A, then D

# Or using systemd
sudo cp leetify-bot.service /etc/systemd/system/
sudo systemctl enable leetify-bot
sudo systemctl start leetify-bot
```
