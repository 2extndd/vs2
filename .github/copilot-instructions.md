<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a Python project for monitoring Vinted marketplace items with Telegram bot integration.

Key features:
- Monitors Vinted marketplace for new items based on configured topics/filters
- Sends notifications via Email, Slack, and Telegram
- Includes Telegram bot commands for status monitoring and control
- Filters items by excluding specific catalog IDs
- Sends photos as attachments in Telegram messages
- Includes item size information in notifications

The project uses:
- requests for HTTP API calls
- python-telegram-bot for Telegram integration
- Email notifications via SMTP
- Rotating file logging
- Threading for concurrent operations

When working with this code:
- Follow Python best practices and PEP 8 style guidelines
- Handle exceptions gracefully with proper logging
- Use type hints where appropriate
- Maintain backwards compatibility with the existing configuration format
