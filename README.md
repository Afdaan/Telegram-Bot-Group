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

### 🤖 General

| Command | Usage | Description |
|---------|-------|-------------|
| `/start` | `/start` | Check if the bot is alive |
| `/help` | `/help` | Show all available commands |
| `/ping` | `/ping` | Check bot latency (ms) |

### 👮 Admin (Group Only)

All admin commands require the user to be a group admin and the bot to have admin permissions.

| Command | Usage | Description |
|---------|-------|-------------|
| `/ban` | `/ban <reply\|@user\|id>` | Permanently ban a user from the group |
| `/unban` | `/unban <reply\|@user\|id>` | Unban a previously banned user |
| `/kick` | `/kick <reply\|@user\|id>` | Kick a user (they can rejoin) |
| `/mute` | `/mute <reply\|@user\|id> [duration]` | Mute a user. Optional duration: `30m`, `2h`, `1d`. Without duration, mute is permanent |
| `/unmute` | `/unmute <reply\|@user\|id>` | Unmute a muted user, restoring all message permissions |
| `/timeout` | `/timeout <reply\|@user\|id> <duration>` | Restrict all permissions for a duration. Duration is required: `30m`, `2h`, `1d` |
| `/warn` | `/warn <reply\|@user\|id> [reason]` | Warn a user. Auto-bans when warn limit is reached (default: 3) |
| `/warns` | `/warns [reply\|@user\|id]` | View warnings for a user. Without target, shows your own warnings |
| `/resetwarns` | `/resetwarns <reply\|@user\|id>` | Clear all warnings for a user |
| `/purge` | `/purge <number>` or `/purge` (reply to message) | Delete messages. Reply-based: deletes all messages from the replied message to the command. Count-based: deletes last N messages. Max: `200` |
| `/pin` | `/pin` (reply to message) | Pin the replied message |
| `/unpin` | `/unpin` (reply to message or standalone) | Unpin a specific message (reply) or all pinned messages (standalone) |

**Duration format:** `<number><unit>` where unit is `m` (minutes), `h` (hours), or `d` (days).
Examples: `30m` = 30 minutes, `2h` = 2 hours, `1d` = 1 day.

### ⚙️ Group Settings (Admin Only)

| Command | Usage | Description |
|---------|-------|-------------|
| `/setup` | `/setup` | Start interactive group configuration wizard |
| `/rules` | `/rules` | Display group rules |
| `/setrules` | `/setrules <rules text>` | Set group rules text |
| `/setwelcome` | `/setwelcome <message>` | Set custom welcome message. Variables: `{name}` (user's name), `{group}` (group title) |
| `/resetwelcome` | `/resetwelcome` | Reset welcome and goodbye messages to default |
| `/slowmode` | `/slowmode <seconds>` | Set slowmode delay. Value: `0` – `3600`. Use `0` to disable |
| `/antiflood` | `/antiflood <limit> [window]` | Configure anti-flood protection. `limit`: message count (use `0` to disable), `window`: time in seconds (default: `10`) |

### 🔖 Filters (Admin Only, Group Only)

| Command | Usage | Description |
|---------|-------|-------------|
| `/filter` | `/filter <trigger> <response>` | Create an auto-response filter. Trigger can be quoted for multi-word: `/filter "hello there" Hi!`. Can also reply to media (photo, video, sticker, document, audio, voice, animation) |
| `/stop` | `/stop <trigger>` | Delete a filter by its trigger |
| `/filters` | `/filters` | List all active filters in the group |

### 🎨 Stickers

| Command | Usage | Description |
|---------|-------|-------------|
| `/kang` | `/kang [emoji]` (reply to photo/sticker) | Add a sticker to your pack. Optional custom emoji, otherwise uses the sticker's original emoji. New users in groups are prompted to DM the bot first to create a pack |
| `/sticker` | `/sticker [emoji]` (reply to photo/sticker) | Alias for `/kang` |
| `/newpack` | `/newpack <pack_name>` (reply to photo/sticker) | Create a new sticker pack with a custom name. The replied media becomes the first sticker |
| `/addsticker` | `/addsticker [emoji] <pack_name>` (reply to photo/sticker) | Add a sticker to a specific named pack. Optional emoji prefix: `/addsticker 🖕 My Pack`. Creates the pack if it doesn't exist |
| `/delsticker` | `/delsticker` (reply to sticker) | Remove a sticker from your pack |
| `/mypacks` | `/mypacks` | List all your sticker packs with links |
| `/tophoto` | `/tophoto` (reply to sticker) | Convert a static sticker to a PNG photo |

> **Note:** Animated and video stickers are not supported for sticker commands.

> **New users:** When using `/kang` or `/addsticker` in a group for the first time, the bot will prompt you to DM it and create your first pack with `/newpack`.

## Plugin Architecture

Each feature is a self-contained plugin in `bot/plugins/`. Plugins are auto-discovered and loaded at startup. To add a new plugin:

1. Create a new `.py` file in the appropriate subdirectory
2. Implement your handlers
3. Export a `register(app)` function that adds handlers to the application

## License

MIT
