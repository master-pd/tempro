
### **📄 bot_commands.md**
```markdown
# Tempro Bot - Complete Command List

## 🤖 Basic Commands

### `/start`
Start the bot and show main menu.

**Usage:** `/start`

**Response:** Welcome message with main menu buttons.

### `/help`
Show help information and available commands.

**Usage:** `/help`

**Response:** Detailed help message with all commands.

### `/about`
Show information about the bot.

**Usage:** `/about`

**Response:** Bot information, version, and features.

## 📧 Email Commands

### `/newemail`
Create a new temporary email address.

**Usage:** `/newemail`

**Response:** Creates and displays a new email address with 1-hour validity.

**Limits:** 10 emails per user, 2 per minute rate limit.

### `/myemails`
List all your email addresses.

**Usage:** `/myemails`

**Response:** Shows list of your active emails with buttons to check/delete.

### `/inbox`
Check email inbox.

**Usage:** 
- `/inbox` - Show email selection
- `/inbox email@domain.com` - Check specific email

**Response:** Shows email messages with options to view/delete.

### `/delete`
Delete an email address.

**Usage:**
- `/delete` - Show email selection for deletion
- `/delete email@domain.com` - Delete specific email

**Response:** Confirmation prompt and deletion result.

## 👑 Pirjada Commands

### `/pirjada`
Access pirjada panel (requires password).

**Usage:** `/pirjada`

**Response:** Asks for pirjada password or shows pirjada panel if already authenticated.

### `/createbot`
Create a new bot (pirjada only).

**Usage:** `/createbot`

**Response:** Guides through bot creation process (token, channel setup).

**Requirements:** Pirjada access, available bot slots.

### `/mybots`
List your created bots (pirjada only).

**Usage:** `/mybots`

**Response:** Shows list of your bots with management options.

## ⚡ Admin Commands

### `/admin`
Access admin panel (admin only).

**Usage:** `/admin`

**Response:** Shows admin dashboard with statistics and controls.

### `/stats`
View detailed statistics (admin only).

**Usage:** `/stats`

**Response:** Shows bot statistics (users, emails, growth, etc.).

### `/broadcast`
Send broadcast message to all users (admin only).

**Usage:** `/broadcast`

**Response:** Guides through broadcast message creation.

### `/maintenance`
Toggle maintenance mode (admin only).

**Usage:** `/maintenance`

**Response:** Enable/disable maintenance mode with custom message.

### `/backup`
Create manual backup (admin only).

**Usage:** `/backup`

**Response:** Creates database backup and notifies admin.

## 🛠️ Utility Commands

### `/status`
Check bot status and system information.

**Usage:** `/status`

**Response:** Shows bot status, system stats, and uptime.

### `/refresh`
Refresh current view.

**Usage:** Click refresh button in menus

**Response:** Updates the current view with latest data.

### `/cancel`
Cancel current operation.

**Usage:** Type `/cancel` during any conversation

**Response:** Cancels the current operation and returns to main menu.

## 📱 Menu Commands (via buttons)

### Main Menu Buttons
- **📧 নতুন ইমেইল**: Create new email
- **📥 আমার ইমেইলগুলো**: List my emails
- **📨 ইমেইল চেক করুন**: Check email inbox
- **👑 পীরজাদা মোড**: Pirjada panel (if pirjada)
- **⚡ এডমিন প্যানেল**: Admin panel (if admin)
- **📢 চ্যানেল**: Show channel link
- **👥 গ্রুপ**: Show group link
- **ℹ️ সাহায্য**: Show help
- **📊 স্ট্যাটাস**: Show status

### Email Management Buttons
- **📥 Check**: Check specific email inbox
- **🗑️ Delete**: Delete specific email
- **🔄 Refresh**: Refresh email list
- **📧 নতুন ইমেইল**: Create new email

### Pirjada Panel Buttons
- **🤖 নতুন বট তৈরি**: Create new bot
- **📊 আমার বটগুলো**: List my bots
- **⚙️ সেটিংস**: Bot settings
- **📈 স্ট্যাটিস্টিক্স**: Statistics
- **🔙 মেনু**: Back to main menu
- **🆘 সাহায্য**: Pirjada help

### Admin Panel Buttons
- **📢 ব্রডকাস্ট**: Send broadcast
- **🛠️ মেইন্টেন্যান্স**: Maintenance mode
- **👥 ইউজার্স**: User management
- **👑 পীরজাদাস**: Pirjada management
- **📊 ডিটেইলড স্ট্যাটস**: Detailed statistics
- **💾 ব্যাকআপ**: Create backup
- **⚙️ সেটিংস**: Admin settings
- **📝 লগস**: View logs
- **🔙 মেনু**: Back to main menu
- **🔄 রিফ্রেশ**: Refresh admin panel

## 🔧 Setup Commands

### First-time Setup
1. Run `python3 setup_wizard.py`
2. Follow interactive prompts
3. Enter bot token, owner ID, etc.
4. Configure channels and settings

### Docker Setup
1. Copy `.env.example` to `.env`
2. Edit `.env` with your settings
3. Run `docker-compose up -d`

### Manual Setup
1. Install requirements: `pip install -r requirements.txt`
2. Create `.env` file with configurations
3. Create `config.json` from example
4. Run `python -m src.main`

## ⚙️ Configuration Commands

### Environment Variables
Key variables in `.env`:
- `BOT_TOKEN`: Telegram bot token
- `OWNER_ID`: Bot owner Telegram ID
- `BOT_USERNAME`: Bot username
- `ADMIN_PASSWORD`: Admin panel password
- `PIRJADA_PASSWORD`: Pirjada access password

### Config Files
- `config/channels.json`: Channel configurations
- `config/social_links.json`: Social media links
- `config/admins.json`: Admin users
- `config/pirjadas.json`: Pirjada users
- `config/bot_mode.json`: Bot mode settings

## 🚨 Emergency Commands

### Force Stop
Press `Ctrl+C` in terminal to stop the bot gracefully.

### Restart Bot
Stop and restart the bot process.

### Reset Database
⚠️ **Dangerous**: Only use if database is corrupted.

### Check Logs
View `logs/bot.log` for debugging information.

## 📊 Statistics Commands

### User Statistics
- Total users
- Active users
- New users today
- User growth rate

### Email Statistics
- Total emails created
- Emails today
- Active emails
- Most used domains

### System Statistics
- Bot uptime
- Memory usage
- CPU usage
- Database size

## 🔒 Security Commands

### Rate Limit View
Check user rate limits.

### User Ban
Ban problematic users.

### Session Clear
Clear user sessions.

### Audit Logs
View security audit logs.

## 🆘 Support Commands

### Report Issue
Report bugs or issues.

### Feature Request
Request new features.

### Contact Admin
Contact bot administrator.

### Documentation
View complete documentation.

## 📁 File Structure Commands

### List Backups
`./run.sh --list-backups`

### Restore Backup
`./run.sh --restore-backup <filename>`

### Check System
`./run.sh --check-system`

### Update Bot
`./run.sh --update`

## ⏰ Scheduled Tasks

### Automatic Backups
Daily at 2 AM.

### Cleanup Tasks
- Expired emails: Every hour
- Inactive users: Every 24 hours
- Old backups: Every 6 hours

### Statistics Update
Every 30 minutes.

## 🔔 Notification Commands

### Email Expiry Notifications
Sent 1 hour before email expiry.

### Pirjada Expiry Notifications
Sent 7, 3, and 1 day before expiry.

### Admin Notifications
For important events and errors.

## 🌐 Social Commands

### Channel Link
`/channel` or click channel button

### Group Link
`/group` or click group button

### Owner Profile
`/owner` or click owner button

### GitHub Repository
`/github` or click GitHub button

---

## Quick Reference Card

### For Users: