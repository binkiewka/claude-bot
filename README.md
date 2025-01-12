# Claude Discord Bot Documentation

Welcome to the Claude Discord Bot documentation. This guide will walk you through the complete setup and deployment process.

## Table of Contents
- [Prerequisites](#prerequisites)
- [API Keys and Credentials](#api-keys-and-credentials)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Bot Commands](#bot-commands)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)

### Required Software Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python (for local development)
sudo apt install python3.11 python3.11-venv
```

## API Keys and Credentials

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Click "Reset Token" and copy your bot token
5. Enable these Privileged Gateway Intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
6. Go to OAuth2 → URL Generator:
   - Select "bot" under scopes
   - Select required permissions:
     - Read Messages/View Channels
     - Send Messages
     - Read Message History
     - Mention Everyone
     - Add Reactions
7. Copy the generated URL - this is your bot invite URL
8. After bot is running, use this URL to invite the bot to your servers:
   - Open the copied URL in a web browser
   - Select the server you want to add the bot to
   - Click "Authorize"
   - Complete the captcha if prompted
   - You should see a confirmation message
   - The bot should now appear in your server's member list

### Anthropic API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or log in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy and save the key securely

### Google Drive API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Drive API
4. Create Service Account:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Fill in the details and click "Create"
   - Add role "Editor" to the service account
5. Create and download JSON key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download and save as `credentials.json`

## Installation

### Directory Setup
```bash
# Create application directory
sudo mkdir -p /opt/claude-bot
sudo mkdir -p /opt/claude-bot/credentials
sudo mkdir -p /opt/claude-bot/logs
sudo mkdir -p /opt/claude-bot/postgres_data

# Set correct permissions
sudo chown -R $(whoami):$(whoami) /opt/claude-bot
sudo chmod -R 755 /opt/claude-bot
```

### Clone Repository
```bash
# Clone the repository
git clone https://github.com/yourusername/claude-bot.git
cd claude-bot

# Copy files to production directory
sudo cp -r * /opt/claude-bot/
```

### Configure Credentials
```bash
# Create environment file
cd /opt/claude-bot
cp .env.example .env

# Edit .env file with your credentials
nano .env

# Add Google Drive credentials
cp path/to/your/credentials.json /opt/claude-bot/credentials/
```

Example `.env` file:
```env
DISCORD_TOKEN=your_discord_token
CLAUDE_API_KEY=your_claude_api_key
POSTGRES_DB_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=claude_bot
POSTGRES_USER=claude
```

## Configuration

### Database Setup
```bash
# Set PostgreSQL data directory permissions
sudo chown -R 999:999 /opt/claude-bot/postgres_data
sudo chmod -R 700 /opt/claude-bot/postgres_data
```

### Bot Configuration
1. Configure AI roles in `/opt/claude-bot/config/ai_roles.yml`
2. Adjust rate limits in `/opt/claude-bot/config/config.py`

## Deployment

### Using Docker Compose
```bash
# Navigate to application directory
cd /opt/claude-bot

# Build containers
docker-compose build --no-cache

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Verifying Deployment
1. Check container status:
```bash
docker-compose ps
```

2. Check application logs:
```bash
docker-compose logs -f claude_bot
```

3. Check database logs:
```bash
docker-compose logs -f postgres
```

## Server Management

### Adding Bot to Servers
1. Ensure the bot is running and online
2. Use the OAuth2 URL generated earlier from Discord Developer Portal
3. For each server you want to add the bot to:
   - Open the OAuth2 URL in a browser
   - Select the target server from the dropdown
   - Click "Authorize"
   - Complete the captcha if prompted
   - Verify the bot appears in the server's member list

### Initial Server Setup
After adding the bot to a server:
1. Use `!setchan` to configure allowed channels
2. Use `!setrole` to set the desired AI role
3. Test the bot by mentioning it in an allowed channel
4. Configure any additional server-specific settings using admin commands

### Managing Multiple Servers
- Each server can have its own:
  - Allowed channels
  - AI role
  - Conversation context
- Use server-specific commands to manage settings
- Monitor usage with `!status` command

## Bot Commands

### Admin Commands
- `!ping` - Check bot latency
- `!status` - Show bot status
- `!admin_status` - Show detailed admin status
- `!setrole <role>` - Set AI role for the server
- `!getrole` - Get current AI role
- `!listroles` - List available AI roles
- `!setchan [#channel]` - Set allowed channel
- `!clearchan` - Clear channel restrictions
- `!listchannels` - List allowed channels

### User Commands
- `!clear_context` - Clear conversation context
- `!claude_status` - Show Claude's status

### Usage
- Mention the bot (@Claude) to start a conversation
- Use commands in any allowed channel
- Bot will only respond in configured channels

## Maintenance

### Backup
1. Database backup:
```bash
# Create backup directory
mkdir -p /opt/claude-bot/backups

# Backup PostgreSQL database
docker exec claude_postgres pg_dump -U claude claude_bot > /opt/claude-bot/backups/claude_bot_$(date +%Y%m%d).sql
```

2. Configuration backup:
```bash
# Backup configuration files
tar -czf /opt/claude-bot/backups/config_$(date +%Y%m%d).tar.gz /opt/claude-bot/config
```

### Updates
```bash
# Stop containers
docker-compose down

# Pull latest changes
git pull

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Log Management
```bash
# View real-time logs
docker-compose logs -f

# Check specific service logs
docker-compose logs -f claude_bot
docker-compose logs -f postgres

# Clear logs
sudo truncate -s 0 /opt/claude-bot/logs/*.log
```

## Troubleshooting

### Common Issues

#### PostgreSQL Permission Issues
If you encounter database permission errors:
```bash
sudo chown -R 999:999 /opt/claude-bot/postgres_data
sudo chmod -R 700 /opt/claude-bot/postgres_data
docker-compose down
docker-compose up -d
```

#### Bot Not Responding
1. Check if bot is online in Discord
2. Verify allowed channels configuration
3. Check logs for errors:
```bash
docker-compose logs -f claude_bot
```

#### Rate Limiting
If hitting rate limits:
1. Check current settings in `config.py`
2. Adjust `max_messages_per_minute` if needed
3. Restart bot to apply changes

### Getting Help
- Check the latest logs
- Review error messages
- Create an issue on GitHub with:
  - Error messages
  - Logs
  - Steps to reproduce
  - Environment details

### Security Considerations
- Keep API keys secure
- Regularly update passwords
- Monitor logs for unusual activity
- Keep system and dependencies updated
- Restrict server access
- Use strong passwords
- Enable Discord audit logs
