# Vinted Scanner & Notifier (Enhanced Version)

## Overview

Vinted Scanner is a Python script designed to automatically search for new items listed on [Vinted](https://www.vinted.com). This enhanced version includes advanced filtering, Telegram bot integration with commands, and improved notification features.

The script runs continuously and sends notifications via **email**, **Slack**, or **Telegram** whenever new items matching your search criteria are found. It also keeps track of already analyzed items to prevent duplicate notifications.

## Enhanced Features

- **Advanced Topic-Based Filtering**: Configure multiple search topics with specific parameters
- **Category Exclusion**: Exclude specific catalog IDs from search results
- **Telegram Bot Commands**: Control and monitor the bot via Telegram commands
- **Photo Attachments**: Telegram notifications include photos as attachments (not links)
- **Size Information**: Item size is included in notifications when available
- **Thread Support**: Send notifications to specific forum threads in Telegram
- **Real-time Status Monitoring**: Check bot status and view logs via commands
- **Graceful Shutdown**: Proper signal handling for clean restarts

## Telegram Bot Commands

- `/status` - Shows bot status and analyzed items count
- `/log` - Sends the last 10 lines from the log file
- `/threadid` - Shows thread IDs for all configured topics
- `/restart` - Restarts the bot

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/VintedScanner.git
   cd VintedScanner
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the `Config.py` file with your settings.

### Configuration

The `Config.py` file contains all configuration options:

#### Telegram Settings
```python
telegram_bot_token = "YOUR_BOT_TOKEN"
telegram_chat_id = "YOUR_CHAT_ID"
```

#### Topic Configuration
Each topic has the following structure:
```python
"Topic Name": {
    "thread_id": 123,  # Telegram thread ID
    "query": {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '',
        'order': 'newest_first',
        'price_to': '100',
    },
    "exclude_catalog_ids": "26, 98, 146, 139"  # Categories to exclude
}
```

#### Search Parameters
- `search_text`: Free text search field
- `catalog_ids`: Specific category IDs to search in (empty = all categories)
- `brand_ids`: Specific brand IDs to search for
- `price_to`: Maximum price filter
- `exclude_catalog_ids`: Categories to exclude from results

## Deployment

### Railway Deployment

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/dYCEUj?referralCode=jKcVeV)

**Automatic Deploy:**
1. Click the "Deploy on Railway" button above
2. Connect your GitHub account if needed
3. Railway will automatically deploy the project
4. The bot will start running immediately

**Manual Deploy:**
1. Create a new Railway project
2. Connect your GitHub repository: `https://github.com/2extndd/vs2`
3. Railway will automatically detect the Python project and deploy using the `Procfile`

**Configuration:**
The bot is pre-configured with Telegram credentials. If you need to change them, you can:
1. Edit the `Config.py` file in your repository, or
2. Set environment variables in Railway (recommended for production):
   - `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
   - `TELEGRAM_CHAT_ID` - Your Telegram chat ID

### Local Deployment

```bash
python vinted_scanner.py
```

The script will run continuously, checking for new items every 60 seconds.

## File Structure

```
VintedScanner/
├── Config.py              # Configuration file
├── vinted_scanner.py      # Main scanner script
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version specification
├── vinted_items.txt      # Tracked items (auto-generated)
├── vinted_scanner.log    # Log file (auto-generated)
└── .github/
    └── copilot-instructions.md
```

## Logging

The script maintains detailed logs in `vinted_scanner.log` with rotation when the file exceeds 5MB. Use the `/log` command to view recent log entries via Telegram.

## Error Handling

The script includes comprehensive error handling:
- Network timeouts and retries
- Graceful degradation when services are unavailable
- Signal handling for clean shutdowns
- Detailed logging for debugging
     smtp_psw = "your_password"
     smtp_server = "smtp.example.com"
     smtp_toaddrs = ["Recipient <recipient@example.com>"]
     smtp_from = "sender@example.com"
     ```

2. **Slack Webhook (for Slack notifications)**:
   - Set the `slack_webhook_url` with your Slack Incoming Webhook URL:
     ```python
     slack_webhook_url = "https://hooks.slack.com/services/..."
     ```

3. **Telegram Bot (for Telegram notifications)**:
   - Set the Telegram bot token and chat ID:
     ```python
     telegram_bot_token = "your_bot_token"
     telegram_chat_id = "your_chat_id"
     ```

4. **Vinted Search Queries**:
   - In the same configuration file, define the queries you want to execute on Vinted. These queries can include search keywords, catalog categories, or specific brands. You can define multiple queries, and the script will iterate through each one:
     ```python
     queries = [
         {
             'page': '1',
             'per_page': '96',
             'search_text': 'jeans',
             'catalog_ids': '',
             'brand_ids' : '417',  # Example brand ID
             'order': 'newest_first',
         },
         {
             'page': '1',
             'per_page': '96',
             'search_text': 't-shirt',
             'catalog_ids': '',
             'brand_ids' : '',
             'order': 'newest_first',
         }
     ]
     ```

   **Notes on search parameters**:
   - `search_text`: Keyword to search (leave blank for all items).
   - `catalog_ids`: Category ID to search in (leave blank for all categories).
   - `brand_ids`: Brand ID to search for a specific brand.
   - `order`: Sorting order (`newest_first`, `relevance`, `price_high_to_low`, `price_low_to_high`).

### Running the Script

To run the script manually, use:

```bash
python3 vinted_scanner.py
```

The script will check for new items based on your queries and send notifications accordingly.

### Automation with Cron

To run the script periodically, you can set up a cron job. For example, to run the script every hour:

1. Open the crontab editor:
   ```bash
   crontab -e
   ```

2. Add the following line to schedule the script to run every hour:
   ```bash
   0 * * * * /usr/bin/python3 /path/to/vinted_scanner.py >> /path/to/logfile.log 2>&1
   ```

This will run the script every hour and log the output to `logfile.log`.

### Logging

Logs are stored in the `vinted_scanner.log` file. The script uses a rotating log handler to ensure that logs don't grow too large.

c### Contributing and Supporting the Project

There are two ways you can contribute to the development of **Tosint**:

1. **Development Contributions**:

   Please ensure that your code follows best practices and includes relevant tests.

2. **Donation Support**:
   If you find this project useful and would like to support its development, you can also make a donation via [Buy Me a Coffee](https://buymeacoffee.com/andreadraghetti). Your support is greatly appreciated and helps to keep this project going!

   [![Buy Me a Coffee](https://img.shields.io/badge/-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee&logoColor=white&style=flat-square)](https://buymeacoffee.com/andreadraghetti)

### License

This project is licensed under the GNU General Public License v3.0.