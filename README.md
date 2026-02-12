# Telegram Group Management Bot

Modular Telegram bot for group administration, sticker management, and more.

## Requirements

- Python 3.10+
- MySQL 8.0+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## Setup

1. **Clone and install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MySQL**
   - Create the database by running `migrations/001_initial.sql`
   - Or let the bot auto-create tables on first run via SQLAlchemy

3. **Create `.env` file**
   ```bash
   cp .env.example .env
   ```
   Fill in your `BOT_TOKEN` and database credentials.

4. **Run the bot**
   ```bash
  ```bash
   python run.py
   ```

5. **Add the bot to your group** and promote it to admin with appropriate permissions.

## Docker Deployment (Recommended)

Running with Docker is highly recommended for reliability and ease of management.

1. **Install Docker and Docker Compose**

2. **Configure `.env`**
   Ensure your `.env` file is set up. Note: `DB_HOST` in `.env` will be overridden to `db` automatically by docker-compose, but other values are used.

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d --build
   ```

   This will:
   - Build the bot container
   - Start a MySQL 8.0 container (data persisted in `db_data` volume)
   - Auto-create the database schema from `migrations/`
   - Restart automatically if the server reboots or the bot crashes

4. **View Logs**
   ```bash
   docker-compose logs -f bot
   ```

## Commands

### Admin Commands
| Command | Description |
|---------|-------------|
| `/mute` | Mute a user (supports timed: `/mute @user 30m`) |
| `/unmute` | Unmute a user |
| `/kick` | Kick a user (can rejoin) |
| `/ban` | Permanently ban a user |
| `/unban` | Unban a user |
| `/timeout` | Restrict all permissions for duration |
| `/warn` | Warn a user (auto-ban at threshold) |
| `/warns` | View warnings for a user |
| `/resetwarns` | Clear all warnings for a user |
| `/purge <n>` | Delete last N messages (max 100) |
| `/pin` | Pin replied message |
| `/unpin` | Unpin message(s) |

### Group Commands
| Command | Description |
|---------|-------------|
| `/rules` | Display group rules |
| `/setrules` | Set group rules |
| `/setwelcome` | Set welcome message (vars: `{name}`, `{group}`) |
| `/resetwelcome` | Reset welcome/goodbye to default |
| `/antiflood` | Configure anti-flood settings |
| `/slowmode` | Set slowmode delay |
| `/setup` | Interactive group configuration |

### Sticker Commands
| Command | Description |
|---------|-------------|
| `/sticker` | Convert photo to sticker (reply to photo) |
| `/tophoto` | Convert sticker to photo (reply to sticker) |
| `/newpack` | Create a new sticker pack |
| `/addsticker` | Add sticker to your pack |
| `/delsticker` | Remove sticker from pack |

## Plugin Architecture

Each feature is a self-contained plugin in `bot/plugins/`. Plugins are auto-discovered and loaded at startup. To add a new plugin:

1. Create a new `.py` file in the appropriate subdirectory
2. Implement your handlers
3. Export a `register(app)` function that adds handlers to the application

## License

MIT
