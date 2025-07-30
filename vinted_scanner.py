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
import asyncio
import threading
import random
from datetime import datetime
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Anti-blocking system
class VintedAntiBlock:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        self.request_count = 0
        self.last_request_time = 0

    def get_random_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    def smart_delay(self):
        """БЫСТРЫЕ задержки между запросами"""
        self.request_count += 1
        current_time = time.time()
        
        # БЫСТРО: 1-3 секунды
        base_delay = random.uniform(1, 3)
        
        # Каждые 20 запросов - короткий перерыв
        if self.request_count % 20 == 0:
            base_delay += random.uniform(5, 10)
            
        logging.info(f"🕐 Delay: {base_delay:.1f}s (#{self.request_count})")
        time.sleep(base_delay)
        self.last_request_time = time.time()

    def handle_rate_limit(self, response):
        """Обработка блокировок"""
        if response.status_code == 429:
            wait_time = random.uniform(120, 300)
            logging.warning(f"🚫 Rate limited! Waiting {wait_time:.0f}s")
            time.sleep(wait_time)
            return True
        elif response.status_code in [403, 406, 503]:
            wait_time = random.uniform(180, 360)
            logging.warning(f"🔒 Blocked! Waiting {wait_time:.0f}s")
            time.sleep(wait_time)
            return True
        return False

# Создаем экземпляр anti-block
anti_block = VintedAntiBlock()

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
scan_mode = "fast"  # "fast" = 15 seconds, "slow" = 45 seconds - БЫСТРЕЕ!
last_errors = []  # Store last errors for status

# Load previously analyzed item hashes to avoid duplicates
def load_analyzed_item():
    try:
        with open("vinted_items.txt", "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    list_analyzed_items.append(line)
        logging.info(f"📥 Loaded {len(list_analyzed_items)} previously analyzed items")
    except IOError as e:
        logging.info("📁 No previous items file found, starting fresh")
        logging.error(e, exc_info=True)

# Add error to last_errors list
def add_error(error_text):
    global last_errors
    timestamp = datetime.now().strftime('%H:%M:%S')
    last_errors.append(f"{timestamp}: {error_text}")
    # Keep only last 5 errors
    if len(last_errors) > 5:
        last_errors = last_errors[-5:]

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
        add_error(f"Email: {str(e)[:50]}")
    except Exception as e:
        logging.error(f"Error sending email: {e}", exc_info=True)
        add_error(f"Email: {str(e)[:50]}")

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
            add_error(f"Slack: {response.status_code}")
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
                add_error(f"TG topic {thread_id}: {response.status_code}")
        
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
            add_error(f"TG main: {response.status_code}")

    except Exception as e:
        add_error(f"TG exception: {str(e)[:50]}")
        logging.error(f"❌ Exception in send_telegram_message: {e}")
        return False

# Send bot status message
def send_bot_status_message(status_text):
    """Send a simple text message about bot status"""
    try:
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        params = {
            "chat_id": Config.telegram_chat_id,
            "text": status_text,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, data=params, timeout=timeoutconnection)
        
        if response.status_code == 200:
            logging.info(f"✅ Status message sent: {status_text}")
            return True
        else:
            logging.error(f"❌ Failed to send status message: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Exception sending status message: {e}")
        return False

# Filter items by exclude_catalog_ids (ИСПРАВЛЕНО)
def should_exclude_item(item, exclude_catalog_ids):
    if not exclude_catalog_ids:
        return False
    
    # Разделяем строку на отдельные ID и очищаем от пробелов
    exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
    item_catalog_id = str(item.get('catalog_id', ''))
    
    # Проверяем точное совпадение
    is_excluded = item_catalog_id in exclude_list
    
    if is_excluded:
        logging.info(f"🚫 Item excluded: catalog_id={item_catalog_id} matches exclude_list={exclude_list}")
    
    return is_excluded

# Telegram bot commands
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    global bot_running, scan_mode, last_errors
    status = "🟢 Бот работает" if bot_running else "🔴 Бот остановлен"
    items_count = len(list_analyzed_items)
    
    # Scan mode info with NEW faster intervals
    mode_emoji = "🐰" if scan_mode == "fast" else "🐌"
    mode_interval = "15 сек" if scan_mode == "fast" else "45 сек"  # БЫСТРЕЕ!
    mode_info = f"\n{mode_emoji} Режим: {scan_mode} (интервал: {mode_interval})"
    
    # Anti-block info
    anti_block_info = f"\n🛡️ Запросов: {anti_block.request_count}"
    anti_block_info += f"\n🔄 User-Agents: {len(anti_block.user_agents)}"
    
    # Error info
    error_info = ""
    if last_errors:
        error_info = f"\n❌ Ошибки:\n" + "\n".join(last_errors[-3:])
    
    response = f"{status}\n📊 Товаров: {items_count}{mode_info}{anti_block_info}{error_info}"
    await update.message.reply_text(response)

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /log command"""
    try:
        with open("vinted_scanner.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-10:] if len(lines) >= 10 else lines
            log_text = "".join(last_lines)
            await update.message.reply_text(f"📝 Лог:\n```\n{log_text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def threadid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /threadid command"""
    message = update.message
    
    if message.is_topic_message and message.message_thread_id:
        topic_name = "Unknown"
        for name, data in Config.topics.items():
            if data.get('thread_id') == message.message_thread_id:
                topic_name = name
                break
        
        response = f"🧵 Thread ID: {message.message_thread_id}\n📍 Топик: {topic_name}"
    else:
        response = "💬 Основной чат\n🧵 Thread ID: None"
    
    await update.message.reply_text(response)

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart command"""
    global bot_running, scanner_thread, list_analyzed_items
    await update.message.reply_text("�� Перезапуск...")
    
    # Stop current scanner
    bot_running = False
    if scanner_thread:
        scanner_thread.join(timeout=5)
    
    # Clear analyzed items list
    old_count = len(list_analyzed_items)
    list_analyzed_items.clear()
    
    try:
        with open("vinted_items.txt", "w") as f:
            f.write("")
        logging.info(f"🗑️ Cleared {old_count} items")
    except Exception as e:
        logging.error(f"Error clearing: {e}")
    
    await asyncio.sleep(2)
    
    # Restart scanner
    bot_running = True
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    
    await update.message.reply_text("✅ Перезапущен!")

async def chatinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chatinfo command"""
    try:
        chat = update.effective_chat
        bot = context.bot
        
        chat_full = await bot.get_chat(chat.id)
        
        info = f"🔍 <b>Диагностика</b>\n"
        info += f"📊 ID: <code>{chat.id}</code>\n"
        info += f"📝 Название: {chat.title or 'N/A'}\n"
        info += f"🏷️ Тип: {chat.type}\n"
        
        if hasattr(chat_full, 'member_count') and chat_full.member_count:
            info += f"👥 Участников: <b>{chat_full.member_count}</b>\n"
            if chat_full.member_count < 200:
                info += f"⚠️ <b>ВНИМАНИЕ:</b> Меньше 200!\n"
        
        if hasattr(chat_full, 'is_forum'):
            info += f"🧵 Форум: {'✅ Да' if chat_full.is_forum else '❌ Нет'}\n"
        
        await update.message.reply_text(info, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def scanner_loop():
    """БЫСТРЫЙ scanner loop с anti-blocking"""
    global bot_running
    
    while bot_running:
        try:
            logging.info("🔄 Новый цикл с защитой от блокировок")
            
            # Получаем динамические заголовки
            session = requests.Session()
            dynamic_headers = anti_block.get_random_headers()
            
            logging.info(f"🔄 User-Agent: {dynamic_headers['User-Agent'][:50]}...")
            
            # Запрос для получения cookies
            session.post(Config.vinted_url, headers=dynamic_headers, timeout=timeoutconnection)
            cookies = session.cookies.get_dict()
            
            # Умная задержка
            anti_block.smart_delay()
            
            # Проходим по всем топикам
            for topic_name, topic_data in Config.topics.items():
                if not bot_running:
                    break
                    
                logging.info(f"🔍 Сканируем: {topic_name}")
                params = topic_data["query"]
                exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
                thread_id = topic_data.get("thread_id")
                
                # Новые заголовки для каждого топика
                topic_headers = anti_block.get_random_headers()
                
                # Запрос к API с защитой
                response = requests.get(f"{Config.vinted_url}/api/v2/catalog/items", 
                                      params=params, cookies=cookies, headers=topic_headers,
                                      timeout=timeoutconnection)

                # Обработка блокировок
                if anti_block.handle_rate_limit(response):
                    continue
                
                if response.status_code == 200:
                    data = response.json()

                    if data and "items" in data:
                        logging.info(f"Найдено {len(data['items'])} товаров: {topic_name}")
                        
                        for item in data["items"]:
                            if not bot_running:
                                break
                                
                            if should_exclude_item(item, exclude_catalog_ids):
                                continue
                                
                            item_id = str(item["id"])
                            item_title = item["title"]
                            item_url = item["url"]
                            item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                            item_image = item["photo"]["full_size_url"]
                            
                            item_size = None
                            if "size_title" in item and item["size_title"]:
                                item_size = item["size_title"]

                            if item_id not in list_analyzed_items:
                                logging.info(f"🆕 НОВЫЙ: {item_title} - {item_price}")

                                # Email
                                if Config.smtp_username and Config.smtp_server:
                                    send_email(item_title, item_price, item_url, item_image, item_size)

                                # Slack
                                if Config.slack_webhook_url:
                                    send_slack_message(item_title, item_price, item_url, item_image, item_size)

                                # Telegram
                                if Config.telegram_bot_token and Config.telegram_chat_id:
                                    success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
                                    if success:
                                        time.sleep(0.5)  # Быстрая задержка

                                list_analyzed_items.append(item_id)
                                save_analyzed_item(item_id)
                    else:
                        logging.warning(f"Нет товаров: {topic_name}")
                else:
                    logging.error(f"Ошибка {response.status_code}: {topic_name}")
                    add_error(f"Vinted {response.status_code}: {topic_name}")
                
                # Задержка между топиками
                if bot_running and len(Config.topics) > 1:
                    delay = random.uniform(0.5, 2)  # Быстро между топиками
                    time.sleep(delay)

            # Быстрые интервалы между циклами
            if bot_running:
                if scan_mode == "fast":
                    delay = random.uniform(15, 25)  # 15-25 сек (было 30)
                    logging.info(f"🐰 FAST: ждем {delay:.0f}s")
                else:
                    delay = random.uniform(45, 60)  # 45-60 сек (было 120)
                    logging.info(f"🐌 SLOW: ждем {delay:.0f}s")
                time.sleep(delay)
                
        except Exception as e:
            add_error(f"Сканнер: {str(e)[:50]}")
            logging.error(f"Ошибка: {e}", exc_info=True)
            if bot_running:
                time.sleep(30)

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global bot_running
    logging.info("Получен сигнал остановки...")
    bot_running = False
    sys.exit(0)

async def fast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fast command"""
    global scan_mode
    scan_mode = "fast"
    await update.message.reply_text("🐰 БЫСТРЫЙ режим\n⏱️ 15-25 секунд")
    logging.info("FAST mode (15-25 seconds)")

async def slow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /slow command"""
    global scan_mode
    scan_mode = "slow"
    await update.message.reply_text("🐌 МЕДЛЕННЫЙ режим\n⏱️ 45-60 секунд")
    logging.info("SLOW mode (45-60 seconds)")

async def setup_bot():
    """Setup Telegram bot"""
    application = Application.builder().token(Config.telegram_bot_token).build()
    
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("threadid", threadid_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("chatinfo", chatinfo_command))
    application.add_handler(CommandHandler("fast", fast_command))
    application.add_handler(CommandHandler("slow", slow_command))
    return application

def main():
    global bot_running, scanner_thread
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    load_analyzed_item()
    
    logging.info("🚀 БЫСТРЫЙ Vinted Scanner с ANTI-BLOCKING!")
    logging.info(f"🛡️ {len(anti_block.user_agents)} User-Agents готово")
    
    # Startup message
    if Config.telegram_bot_token and Config.telegram_chat_id:
        items_count = len(list_analyzed_items)
        total_topics = len(Config.topics)
        startup_msg = f"🟢 <b>БОТ ЗАПУЩЕН С ЗАЩИТОЙ</b>\n📊 Товаров: {items_count}\n🚀 Топиков: {total_topics}\n🛡️ Anti-block: ON\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        send_bot_status_message(startup_msg)
    
    # Start scanner
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    
    # Start bot
    if Config.telegram_bot_token and Config.telegram_chat_id:
        try:
            async def run_bot():
                application = await setup_bot()
                await application.initialize()
                await application.start()
                await application.updater.start_polling(drop_pending_updates=True)
                
                while bot_running:
                    await asyncio.sleep(1)
                    
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
            
            asyncio.run(run_bot())
            
        except KeyboardInterrupt:
            logging.info("Остановлен пользователем")
        except Exception as e:
            logging.error(f"Ошибка бота: {e}", exc_info=True)
            try:
                while bot_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Сканнер остановлен")
    else:
        try:
            while bot_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Сканнер остановлен")

if __name__ == "__main__":
    main()
