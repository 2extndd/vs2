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
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
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
        
        # Add topic info to message if thread_id is used
        topic_info = ""
        if thread_id:
            # Find topic name by thread_id
            topic_name = "Unknown"
            for name, data in Config.topics.items():
                if data.get('thread_id') == thread_id:
                    topic_name = name
                    break
            topic_info = f"\n🏷️ Топик: {topic_name}"
        
        message = f"<b>{item_title}</b>\n🏷️ {item_price}{size_text}{topic_info}\n🔗 {item_url}"

        # First try: Send to topic if thread_id provided
        if thread_id:
            params_topic = {
                "chat_id": Config.telegram_chat_id,
                "photo": item_image,
                "caption": message,
                "parse_mode": "HTML",
                "message_thread_id": thread_id
            }
            
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
            logging.info(f"🎯 Trying to send to topic {thread_id}")
            
            response = requests.post(url, data=params_topic, timeout=timeoutconnection)
            
            if response.status_code == 200:
                logging.info(f"✅ SUCCESS: Sent to topic {thread_id}")
                return True
            else:
                logging.warning(f"❌ FAILED to send to topic {thread_id}: {response.status_code} - {response.text}")
        
        # Fallback: Send to main chat
        params_main = {
            "chat_id": Config.telegram_chat_id,
            "photo": item_image,
            "caption": message + "\n⚠️ Отправлено в основной чат",
            "parse_mode": "HTML",
        }
        
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
        logging.info(f"🔄 Sending to main chat as fallback")
        
        response = requests.post(url, data=params_main, timeout=timeoutconnection)
        
        if response.status_code == 200:
            logging.info(f"✅ SUCCESS: Sent to main chat")
            return True
        else:
            logging.error(f"❌ FAILED to send to main chat: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logging.error(f"❌ Exception in send_telegram_message: {e}")
        return False

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
    thread_info = "🧵 Configured Thread IDs:\n"
    for topic_name, topic_data in Config.topics.items():
        thread_info += f"• {topic_name}: {topic_data['thread_id']}\n"
    
    thread_info += f"\n💬 Chat ID: {Config.telegram_chat_id}"
    thread_info += f"\n🤖 Bot Token: {Config.telegram_bot_token[:20]}..."
    thread_info += "\n\n⚠️ Если thread не найден, сообщения отправляются в основной чат"
    
    await update.message.reply_text(thread_info)

async def chat_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chatinfo command - get chat information"""
    try:
        bot = Bot(token=Config.telegram_bot_token)
        chat = await bot.get_chat(chat_id=Config.telegram_chat_id)
        
        info = f"📊 Информация о чате:\n"
        info += f"• ID: {chat.id}\n"
        info += f"• Тип: {chat.type}\n"
        info += f"• Название: {chat.title}\n"
        info += f"• Описание: {chat.description or 'Нет'}\n"
        
        if hasattr(chat, 'is_forum'):
            info += f"• Форум: {'Да' if chat.is_forum else 'Нет'}\n"
        
        # Check if bot can send messages to topics
        if chat.type == 'supergroup':
            info += f"• Супергруппа: Да\n"
            
        await update.message.reply_text(info)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения информации о чате: {e}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command - send test notification"""
    # Check if user provided thread_id argument
    args = context.args
    test_thread_id = None
    
    if args:
        try:
            test_thread_id = int(args[0])
            await update.message.reply_text(f"🧪 Отправляю тестовое уведомление в топик {test_thread_id}...")
        except ValueError:
            await update.message.reply_text("❌ Неверный формат thread_id. Используйте: /test <thread_id>")
            return
    else:
        # Test with first topic's thread_id
        first_topic = next(iter(Config.topics.values()))
        test_thread_id = first_topic.get('thread_id')
        await update.message.reply_text(f"🧪 Отправляю тестовое уведомление в топик {test_thread_id} (первый из конфига)...")
    
    # Send test notification
    test_title = "🧪 Тестовое уведомление"
    test_price = "99.99 EUR"
    test_url = "https://vinted.com/test"
    test_image = "https://images.vinted.net/thumbs/f800/01_00_8c2/01_00_8c2.jpeg"
    test_size = "M"
    
    # Test with specified thread_id
    send_telegram_message(test_title, test_price, test_url, test_image, test_size, test_thread_id)
    
    await update.message.reply_text(f"✅ Тест отправлен в thread {test_thread_id}")

async def test_main_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /testmain command - send test to main chat"""
    await update.message.reply_text("🧪 Отправляю тестовое уведомление в основной чат...")
    
    # Send test notification to main chat (no thread_id)
    test_title = "🧪 Тестовое уведомление (основной чат)"
    test_price = "99.99 EUR" 
    test_url = "https://vinted.com/test"
    test_image = "https://images.vinted.net/thumbs/f800/01_00_8c2/01_00_8c2.jpeg"
    test_size = "M"
    
    send_telegram_message(test_title, test_price, test_url, test_image, test_size, None)
    
    await update.message.reply_text("✅ Тест отправлен в основной чат")

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /config command - show current configuration"""
    config_info = "⚙️ Текущая конфигурация:\n\n"
    config_info += f"🌐 Vinted URL: {Config.vinted_url}\n"
    config_info += f"💬 Chat ID: {Config.telegram_chat_id}\n"
    config_info += f"🧵 Топиков настроено: {len(Config.topics)}\n\n"
    
    config_info += "📝 Топики:\n"
    for topic_name, topic_data in list(Config.topics.items())[:5]:  # Show first 5
        thread_id = topic_data.get('thread_id')
        config_info += f"• {topic_name}: thread {thread_id}\n"
    
    if len(Config.topics) > 5:
        config_info += f"... и еще {len(Config.topics) - 5} топиков\n"
    
    config_info += f"\n🔄 Интервал сканирования: 60 секунд"
    
    await update.message.reply_text(config_info)

async def check_topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checktopics command - check if topics exist"""
    await update.message.reply_text("🔍 Проверяю доступность топиков...")
    
    try:
        bot = Bot(token=Config.telegram_bot_token)
        
        # Get chat info
        chat = await bot.get_chat(chat_id=Config.telegram_chat_id)
        
        info = f"📊 Информация о чате:\n"
        info += f"• ID: {chat.id}\n"
        info += f"• Тип: {chat.type}\n"
        info += f"• Название: {chat.title or 'Без названия'}\n"
        
        # Check if it's a forum
        is_forum = getattr(chat, 'is_forum', False)
        info += f"• Форум: {'✅ Да' if is_forum else '❌ Нет'}\n"
        
        if not is_forum:
            info += "\n⚠️ ПРОБЛЕМА: Чат не настроен как форум!\n"
            info += "Для использования топиков нужно:\n"
            info += "1. Зайти в настройки группы\n"
            info += "2. Включить 'Topics' (Топики)\n"
            info += "3. Создать нужные топики\n"
        
        await update.message.reply_text(info)
        
        # Test a simple message without thread
        test_text = "🧪 Тест связи с чатом"
        
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        params = {
            "chat_id": Config.telegram_chat_id,
            "text": test_text
        }
        
        response = requests.post(url, data=params, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_text("✅ Связь с чатом работает")
        else:
            await update.message.reply_text(f"❌ Проблема с отправкой: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def debug_topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /debug command - test all topics"""
    await update.message.reply_text("🔍 Тестирую все топики из конфигурации...")
    
    results = []
    for topic_name, topic_data in Config.topics.items():
        thread_id = topic_data.get('thread_id')
        
        # Send test message to each topic
        test_title = f"🔍 Debug: {topic_name}"
        test_price = "Debug EUR"
        test_url = "https://vinted.com/debug"
        test_image = "https://images.vinted.net/thumbs/f800/01_00_8c2/01_00_8c2.jpeg"
        test_size = "Debug"
        
        success = send_telegram_message(test_title, test_price, test_url, test_image, test_size, thread_id)
        
        status = "✅" if success else "❌"
        results.append(f"{status} {topic_name} (thread: {thread_id})")
        
        # Small delay between messages
        import asyncio
        await asyncio.sleep(1)
    
    result_text = "📊 Результаты тестирования топиков:\n\n" + "\n".join(results)
    await update.message.reply_text(result_text)

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
                                logging.info(f"🆕 NEW ITEM FOUND: {item_title} - {item_price}")
                                logging.info(f"📍 Topic: {topic_name}, Thread ID: {thread_id}")

                                # Send e-mail notifications if configured
                                if Config.smtp_username and Config.smtp_server:
                                    send_email(item_title, item_price, item_url, item_image, item_size)

                                # Send Slack notifications if configured
                                if Config.slack_webhook_url:
                                    send_slack_message(item_title, item_price, item_url, item_image, item_size)

                                # Send Telegram notifications if configured
                                if Config.telegram_bot_token and Config.telegram_chat_id:
                                    logging.info(f"🚀 SENDING TO TELEGRAM: topic={topic_name}, thread={thread_id}")
                                    success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
                                    if success:
                                        logging.info(f"✅ TELEGRAM SUCCESS for {topic_name}")
                                    else:
                                        logging.error(f"❌ TELEGRAM FAILED for {topic_name}")

                                # Mark item as analyzed and save it
                                list_analyzed_items.append(item_id)
                                save_analyzed_item(item_id)
                                
                                logging.info(f"✅ Item processed and saved: {item_title}")
                            else:
                                logging.debug(f"⏭️ Item {item_id} already analyzed, skipping")
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
    application.add_handler(CommandHandler("chatinfo", chat_info_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("testmain", test_main_command))
    application.add_handler(CommandHandler("checktopics", check_topics_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("debug", debug_topics_command))
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
