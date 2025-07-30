#!/usr/bin/env python3
import sys
import time
import json
import Config
import smtplib
import logging
import requests
import email.utils
import os
import signal
import threading
from datetime import datetime
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Override config with environment variables if available (for Railway)
if os.getenv('TELEGRAM_BOT_TOKEN'):
    Config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
if os.getenv('TELEGRAM_CHAT_ID'):
    Config.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')


# Configure a rotating file handler to manage log files
handler = RotatingFileHandler("vinted_scanner.log", maxBytes=5000000, backupCount=5)

logging.basicConfig(handlers=[handler], 
                    format="%(asctime)s - %(filename)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s", 
                    level=logging.INFO)

# Timeout configuration for the requests
timeoutconnection = 30

# List to keep track of already analyzed items
list_analyzed_items = []

# Global variables for bot status
bot_running = True
scanner_thread = None

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

# Load previously analyzed item hashes to avoid duplicates
def load_analyzed_item():
    try:
        with open("vinted_items.txt", "r", errors="ignore") as f:
            for line in f:
                if line:
                    list_analyzed_items.append(line.rstrip())
    except IOError as e:
        logging.error(e, exc_info=True)

# Save a new analyzed item to prevent repeated alerts
def save_analyzed_item(hash):
    try:
        with open("vinted_items.txt", "a") as f:
            f.write(str(hash) + "\n")
    except IOError as e:
        logging.error(e, exc_info=True)

# Send notification e-mail when a new item is found
def send_email(item_title, item_price, item_url, item_image, item_size=None):
    try:
        # Create the e-mail message
        msg = EmailMessage()
        msg["To"] = Config.smtp_toaddrs
        msg["From"] = email.utils.formataddr(("Vinted Scanner", Config.smtp_username))
        msg["Subject"] = "Vinted Scanner - New Item"
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        # Format message content
        size_text = f"\n👕 Размер: {item_size}" if item_size else ""
        body = f"{item_title}\n🏷️ {item_price}{size_text}\n🔗 {item_url}\n📷 {item_image}"

        msg.set_content(body)
        
        # Securely opening the SMTP connection
        with smtplib.SMTP(Config.smtp_server, 587) as smtpserver:
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()

            # Authentication
            smtpserver.login(Config.smtp_username, Config.smtp_psw)
            
            # Sending the message
            smtpserver.send_message(msg)
            logging.info("E-mail sent")
    
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error sending email: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Error sending email: {e}", exc_info=True)


# Send a Slack message when a new item is found
def send_slack_message(item_title, item_price, item_url, item_image, item_size=None):
    webhook_url = Config.slack_webhook_url 

    # Format message content
    size_text = f"\n👕 Размер: {item_size}" if item_size else ""
    message = f"*{item_title}*\n🏷️ {item_price}{size_text}\n🔗 {item_url}\n📷 {item_image}"
    slack_data = {"text": message}

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
            timeout=timeoutconnection
        )

        if response.status_code != 200:
            logging.error(f"Slack notification failed: {response.status_code}, {response.text}")
        else:
            logging.info("Slack notification sent")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Slack message: {e}")

# Send a Telegram message with photo as attachment when a new item is found
def send_telegram_message(item_title, item_price, item_url, item_image, item_size=None, thread_id=None):
    try:
        # Format message content
        size_text = f"\n👕 Размер: {item_size}" if item_size else ""
        message = f"<b>{item_title}</b>\n🏷️ {item_price}{size_text}\n🔗 {item_url}"

        # Send photo with caption using direct HTTP request to avoid bot conflicts
        params = {
            "chat_id": Config.telegram_chat_id,
            "photo": item_image,
            "caption": message,
            "parse_mode": "HTML",
        }
        
        # Add thread_id if provided
        if thread_id:
            params["message_thread_id"] = thread_id

        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
        
        response = requests.post(url, data=params, timeout=timeoutconnection)
        if response.status_code != 200:
            logging.error(f"Telegram notification failed. Status code: {response.status_code}, Response: {response.text}")
        else:
            logging.info(f"Telegram notification sent to chat {Config.telegram_chat_id}, thread: {thread_id}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message: {e}")

# Filter items by exclude_catalog_ids
def should_exclude_item(item, exclude_catalog_ids):
    if not exclude_catalog_ids:
        return False
    
    exclude_list = [id.strip() for id in exclude_catalog_ids.split(',')]
    item_catalog_id = str(item.get('catalog_id', ''))
    
    return item_catalog_id in exclude_list

# Telegram bot commands
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    global bot_running
    status = "🟢 Бот работает" if bot_running else "🔴 Бот остановлен"
    items_count = len(list_analyzed_items)
    await update.message.reply_text(f"{status}\n📊 Проанализировано товаров: {items_count}")

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /log command"""
    try:
        with open("vinted_scanner.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-10:] if len(lines) >= 10 else lines
            log_text = "".join(last_lines)
            await update.message.reply_text(f"📝 Последние 10 строк лога:\n```\n{log_text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка чтения лога: {e}")

async def threadid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /threadid command"""
    thread_info = "🧵 Thread IDs:\n"
    for topic_name, topic_data in Config.topics.items():
        thread_info += f"• {topic_name}: {topic_data['thread_id']}\n"
    await update.message.reply_text(thread_info)

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart command"""
    global bot_running, scanner_thread
    await update.message.reply_text("🔄 Перезапускаю бота...")
    bot_running = False
    if scanner_thread:
        scanner_thread.join(timeout=5)
    bot_running = True
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    await update.message.reply_text("✅ Бот перезапущен")

def scanner_loop():
    """Main scanner loop that runs in a separate thread"""
    global bot_running
    
    while bot_running:
        try:
            # Initialize session and obtain session cookies from Vinted
            session = requests.Session()
            session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
            cookies = session.cookies.get_dict()
            
            # Loop through each topic defined in Config.py
            for topic_name, topic_data in Config.topics.items():
                if not bot_running:
                    break
                    
                logging.info(f"Scanning topic: {topic_name}")
                params = topic_data["query"]
                exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
                thread_id = topic_data.get("thread_id")
                
                # Request items from the Vinted API based on the search parameters
                response = requests.get(f"{Config.vinted_url}/api/v2/catalog/items", 
                                      params=params, cookies=cookies, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if data and "items" in data:
                        logging.info(f"Found {len(data['items'])} items for topic {topic_name}")
                        # Process each item returned in the response
                        for item in data["items"]:
                            if not bot_running:
                                break
                                
                            # Check if item should be excluded
                            if should_exclude_item(item, exclude_catalog_ids):
                                logging.debug(f"Item {item['id']} excluded by catalog filter")
                                continue
                                
                            item_id = str(item["id"])
                            item_title = item["title"]
                            item_url = item["url"]
                            item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                            item_image = item["photo"]["full_size_url"]
                            
                            # Get item size if available
                            item_size = None
                            if "size_title" in item and item["size_title"]:
                                item_size = item["size_title"]

                            # Check if the item has already been analyzed to prevent duplicates
                            if item_id not in list_analyzed_items:
                                logging.info(f"Processing new item: {item_title} - {item_price}")

                                # Send e-mail notifications if configured
                                if Config.smtp_username and Config.smtp_server:
                                    send_email(item_title, item_price, item_url, item_image, item_size)

                                # Send Slack notifications if configured
                                if Config.slack_webhook_url:
                                    send_slack_message(item_title, item_price, item_url, item_image, item_size)

                                # Send Telegram notifications if configured
                                if Config.telegram_bot_token and Config.telegram_chat_id:
                                    send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)

                                # Mark item as analyzed and save it
                                list_analyzed_items.append(item_id)
                                save_analyzed_item(item_id)
                                
                                logging.info(f"New item processed: {item_title} - {item_price}")
                            else:
                                logging.debug(f"Item {item_id} already analyzed, skipping")
                    else:
                        logging.warning(f"No items found for topic {topic_name}")
                else:
                    logging.error(f"Failed to fetch items for topic {topic_name}: {response.status_code}")

            # Wait before next scan (60 seconds)
            if bot_running:
                time.sleep(60)
                
        except Exception as e:
            logging.error(f"Error in scanner loop: {e}", exc_info=True)
            if bot_running:
                time.sleep(30)  # Wait before retrying

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global bot_running
    logging.info("Received shutdown signal, stopping bot...")
    bot_running = False
    sys.exit(0)

async def setup_bot():
    """Setup Telegram bot with commands"""
    # Create application
    application = Application.builder().token(Config.telegram_bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("threadid", threadid_command))
    application.add_handler(CommandHandler("restart", restart_command))
    
    return application

def main():
    global bot_running, scanner_thread
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load the list of previously analyzed items
    load_analyzed_item()
    
    logging.info("Starting Vinted Scanner with Telegram bot...")
    
    # Start scanner in separate thread
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    
    # Start Telegram bot if configured (only for commands, not for notifications)
    if Config.telegram_bot_token and Config.telegram_chat_id:
        try:
            import asyncio
            
            async def run_bot():
                application = await setup_bot()
                await application.initialize()
                await application.start()
                
                # Start polling with drop_pending_updates=True to avoid conflicts
                await application.updater.start_polling(drop_pending_updates=True)
                
                # Keep the bot running
                while bot_running:
                    await asyncio.sleep(1)
                    
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
            
            asyncio.run(run_bot())
            
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
        except Exception as e:
            logging.error(f"Error running Telegram bot: {e}", exc_info=True)
            # If bot fails, continue with just scanner
            try:
                while bot_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Scanner stopped by user")
    else:
        # If no Telegram bot, just run scanner
        try:
            while bot_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Scanner stopped by user")

if __name__ == "__main__":
    main()
