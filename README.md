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
| `/afk` | `/afk [reason]` | Mark yourself as AFK. Also triggers on `brb`. When mentioned or replied to, others are notified. Auto-clears when you send a message |
| `s/find/replace` | `s/typo/fix` (reply) | Sed/regex: reply to a message to correct text. Flags: `i` (ignore case), `g` (global). Delimiters: `/` `:` `\|` `_` |
| `/tr` | `/tr <lang>` (reply) or `/tr <lang> <text>` | Translate text using Google Translate. Auto-detects source language. Example: `/tr en`, `/tr ja hello world` |
| `/userinfo` | `/userinfo [reply\|@user\|id]` | Detailed user info: ID, name, username, Telegram bio, group status, custom title, warnings, profile photo |

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
| `/warn` | `/warn <reply\|@user\|id> [reason]` | Warn a user. Auto-bans/kicks when warn limit is reached (default: 3). Shows inline "Remove Warn" button for admins |
| `/warns` | `/warns [reply\|@user\|id]` | View warnings for a user with reasons and dates |
| `/resetwarns` | `/resetwarns <reply\|@user\|id>` | Clear all warnings for a user |
| `/warnlimit` | `/warnlimit <number>` | Set the warn limit (minimum: 3). Without argument shows current setting |
| `/strongwarn` | `/strongwarn <on\|off>` | `on` = ban on limit, `off` = kick on limit |
| `/addwarn` | `/addwarn <keyword> <reason>` | Auto-warn when keyword is detected. Use quotes for multi-word: `/addwarn "bad word" reason` |
| `/nowarn` | `/nowarn <keyword>` | Remove a warn filter. Also: `/stopwarn`, `/rmwarn` |
| `/warnlist` | `/warnlist` | List all active warn filters. Also: `/warnfilters` |
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
| `/slowmode` | `/slowmode on\|off` or `/slowmode <seconds>` | Enable/disable slowmode or set custom delay. `on` uses previous or default (30s). Value: `0` – `3600` |
| `/antiflood` | `/antiflood on\|off` or `/antiflood <limit> [window]` | Enable/disable anti-flood or set custom values. `on` uses previous or default settings (5 msgs / 10s). Minimum limit: `3` |
| `/flood` | `/flood` | Check current anti-flood status and settings (any member can use) |
| `/reports` | `/reports on\|off` | Enable/disable user reporting. Default: enabled |
| `/report` | `/report [reason]` (reply) | Report a message to admins. Also triggers on `@admin`. Admins get a DM with a link to the message |

### 🔖 Filters (Admin Only, Group Only)

| Command | Usage | Description |
|---------|-------|-------------|
| `/filter` | `/filter <trigger> <response>` | Create an auto-response filter. Trigger can be quoted for multi-word: `/filter "hello there" Hi!`. Can also reply to media (photo, video, sticker, document, audio, voice, animation) |
| `/stop` | `/stop <trigger>` | Delete a filter by its trigger |
| `/filters` | `/filters` | List all active filters in the group |

### 🚫 Blacklist (Admin Only, Group Only)

| Command | Usage | Description |
|---------|-------|-------------|
| `/blacklist` | `/blacklist` | View all blacklisted words (any member can view) |
| `/addblacklist` | `/addblacklist <word>` | Add word(s) to blacklist. Separate multiple words with new lines |
| `/rmblacklist` | `/rmblacklist <word>` | Remove word(s) from blacklist. Also: `/unblacklist` |

> **Note:** Messages containing blacklisted words are auto-deleted. Admins are exempt from blacklist filtering.

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

### 📡 RSS Feeds (Group Only)

| Command | Usage | Description |
|---------|-------|-------------|
| `/rss` | `/rss <link>` | Preview an RSS feed's info and latest entry |
| `/listrss` | `/listrss` | List all RSS subscriptions for this group |
| `/addrss` | `/addrss <link>` | Subscribe to an RSS feed (admin only). Bot checks for updates every 2 minutes |
| `/removerss` | `/removerss <link>` | Unsubscribe from an RSS feed (admin only) |

> **GitHub example:** `/addrss https://github.com/user/repo/releases.atom`

## Plugin Architecture

Each feature is a self-contained plugin in `bot/plugins/`. Plugins are auto-discovered and loaded at startup. To add a new plugin:

1. Create a new `.py` file in the appropriate subdirectory
2. Implement your handlers
3. Export a `register(app)` function that adds handlers to the application

## License

MIT
