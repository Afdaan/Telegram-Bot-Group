# 📜 Telegram Bot Commands

This document provides a comprehensive list of all available commands for this Telegram management bot.

## 🤖 General Commands
| Command | Usage | Description |
|---------|-------|-------------|
| `/start` | `/start` | Initialize interaction with the bot |
| `/help` | `/help` | Open the interactive help menu |
| `/ping` | `/ping` | Check bot latency and server status |
| `/afk` | `/afk [reason]` | Set an away-from-keyboard status |
| `/userinfo` | `/userinfo [reply|@user|id]` | View detailed profile and metadata |

## 👮 Admin & Moderation
| Command | Usage | Description |
|---------|-------|-------------|
| `/ban` | `/ban <reply|id>` | Permanently ban a user from the group |
| `/unban` | `/unban <reply|id>` | Restore access for a banned user |
| `/mute` | `/mute <reply|id> [time]` | Restrict user from sending messages |
| `/kick` | `/kick <reply|id>` | Remove user temporarily from the group|
| `/warn` | `/warn <reply|id> [reason]` | Issue a warning to a user |
| `/resetwarns`| `/resetwarns <reply>` | Clear all warnings for a user |
| `/purge` | `/purge <num>` | Delete a specific number of messages |

## ⚙️ Group Configuration
| Command | Usage | Description |
|---------|-------|-------------|
| `/setup` | `/setup` | Launch the setup wizard |
| `/rules` | `/rules` | View group rules |
| `/setrules` | `/setrules <text>` | Update group rules |
| `/slowmode` | `/slowmode <sec>` | Adjust message cooldown for members |
| `/antiflood`| `/antiflood <on|off>`| Toggle flood protection system |

## 🛠️ Utility Tools
| Command | Usage | Description |
|---------|-------|-------------|
| `/tr` | `/tr <lang>` (reply) | Translate content using Google API |
| `/wiki` | `/wiki <query>` | Search Wikipedia for summaries |
| `/calc` | `/calc <expression>` | Evaluate mathematical operations |
| `/qr` | `/qr <text>` | Generate a high-quality QR code |
| `/ud` | `/ud <word>` | Look up definitions on Urban Dictionary |

## 🎭 Entertainment
| Command | Usage | Description |
|---------|-------|-------------|
| `/decide` | `/decide <A> or <B>` | Let the bot make a choice for you |
| `/slap` | `/slap` (reply) | Perform a social slap action |
| `/kill` | `/kill` (reply) | Fake-execute a group member |
| `/ship` | `/ship` (reply) | Calculate love compatibility |
| `/iq` | `/iq` | Check daily IQ scores |
| `/roll` | `/roll [max]` | Roll a randomized dice |

## 🎨 Sticker Management
| Command | Usage | Description |
|---------|-------|-------------|
| `/kang` | `/kang` (reply) | Add stickers to your primary pack |
| `/newpack` | `/newpack <name>` | Initialize a new custom sticker pack |
| `/addsticker`| `/addsticker <name>` | Append media to a specific pack |
| `/mypacks` | `/mypacks` | List all packs created by the user |
| `/tophoto` | `/tophoto` (reply) | Convert stickers to PNG images |

## 📡 RSS & Automation
| Command | Usage | Description |
|---------|-------|-------------|
| `/addrss` | `/addrss <url>` | Subscribe group to an RSS feed |
| `/listrss` | `/listrss` | View all active RSS subscriptions |
| `/removerss`| `/removerss <url>`| Discontinue an RSS subscription |
| `/filters` | `/filters` | Manage automated trigger responses |
