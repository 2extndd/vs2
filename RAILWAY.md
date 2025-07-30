# Railway Deployment Guide

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

## Manual Deployment

1. Fork this repository to your GitHub account
2. Go to [Railway](https://railway.app)
3. Click "Deploy from GitHub repo"
4. Select your forked repository
5. Railway will automatically detect the Python project and start deployment

## Environment Variables

No environment variables needed - all configuration is in `Config.py`.

## Configuration

After deployment, you can modify the `Config.py` file to customize:
- Telegram bot token and chat ID
- Search topics and filters
- Notification preferences

## Monitoring

The bot includes several Telegram commands for monitoring:
- `/status` - Check bot status
- `/log` - View recent logs
- `/threadid` - Show thread IDs
- `/restart` - Restart the bot

## Logs

Logs are automatically rotated and can be viewed via the `/log` command or Railway's web interface.

## Support

For issues and questions, please open an issue on GitHub.
