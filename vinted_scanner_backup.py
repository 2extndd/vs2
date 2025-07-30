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

# Override config with environment variables if available (for Railway)
if os.getenv('TELEGRAM_BOT_TOKEN'):
    Config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
if os.getenv('TELEGRAM_CHAT_ID'):
    Config.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Configure logging
handler = RotatingFileHandler("vinted_scanner.log", maxBytes=5000000, backupCount=3)
logging.basicConfig(handlers=[handler], 
                    format="%(asctime)s - %(levelname)s - %(message)s", 
                    level=logging.INFO)

# Global variables
timeoutconnection = 30
list_analyzed_items = []
bot_running = True
scanner_thread = None
scan_mode = "fast"  # "fast" = 5-7s priority, 10-15s normal, "slow" = 15-20s priority, 30-45s normal
last_errors = []
telegram_errors = []
vinted_errors = []

# PRIORITY TOPICS - these scan more frequently
PRIORITY_TOPICS = ["bags", "bags 2"]

# ANTI-BLOCKING SYSTEM FOR VINTED
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

    def get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }

    def delay(self):
        """Быстрые задержки 0.5-2 сек"""
        self.request_count += 1
        delay = random.uniform(0.5, 2.0)
        if self.request_count % 10 == 0:
            delay += random.uniform(2, 5)
        time.sleep(delay)

    def handle_errors(self, response):
        """Обработка ошибок"""
        if response.status_code == 429:
            wait = random.uniform(60, 120)
            logging.warning(f"Rate limit! Wait {wait:.0f}s")
            time.sleep(wait)
            return True
        elif response.status_code in [403, 503]:
            wait = random.uniform(30, 60)
            logging.warning(f"Blocked! Wait {wait:.0f}s")
            time.sleep(wait)
            return True
        return False

# ANTI-BLOCKING SYSTEM FOR TELEGRAM
class TelegramAntiBlock:
    def __init__(self):
        self.message_count = 0
        self.last_message_time = 0
        
    def safe_delay(self):
        """СТРОГО 1 СЕКУНДА между сообщениями + защита от флуда"""
        self.message_count += 1
        current_time = time.time()
        
        # Минимум 1 секунда между сообщениями
        time_since_last = current_time - self.last_message_time
        if time_since_last < 1.0:
            sleep_time = 1.0 - time_since_last
            time.sleep(sleep_time)
        
        # Дополнительная защита: каждые 20 сообщений - пауза 3-5 сек
        if self.message_count % 20 == 0:
            extra_delay = random.uniform(3, 5)
            logging.info(f"🛡️ TG Anti-flood: {extra_delay:.1f}s pause after {self.message_count} messages")
            time.sleep(extra_delay)
        
        self.last_message_time = time.time()

# Global instances
vinted_antiblock = VintedAntiBlock()
telegram_antiblock = TelegramAntiBlock()

def load_analyzed_item():
    try:
        with open("vinted_items.txt", "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    list_analyzed_items.append(line)
        logging.info(f"Loaded {len(list_analyzed_items)} items")
    except:
        logging.info("Starting fresh")

def save_analyzed_item(item_id):
    try:
        with open("vinted_items.txt", "a") as f:
            f.write(str(item_id) + "\n")
    except Exception as e:
        logging.error(f"Save error: {e}")

def add_error(error_text, error_type="general"):
    global last_errors, telegram_errors, vinted_errors
    timestamp = datetime.now().strftime('%H:%M:%S')
    error_entry = f"{timestamp}: {error_text}"
    
    last_errors.append(error_entry)
    if len(last_errors) > 3:
        last_errors = last_errors[-3:]
    
    if error_type == "telegram":
        telegram_errors.append(timestamp)
        if len(telegram_errors) > 10:
            telegram_errors = telegram_errors[-10:]
    elif error_type == "vinted":
        vinted_errors.append(timestamp)
        if len(vinted_errors) > 10:
            vinted_errors = vinted_errors[-10:]

def send_email(item_title, item_price, item_url, item_image, item_size=None):
    try:
        msg = EmailMessage()
        msg["To"] = Config.smtp_toaddrs
        msg["From"] = email.utils.formataddr(("Vinted Scanner", Config.smtp_username))
        msg["Subject"] = "Vinted Scanner - New Item"
        
        size_text = f"\n👕 {item_size}" if item_size else ""
        body = f"{item_title}\n🏷️ {item_price}{size_text}\n🔗 {item_url}"
        msg.set_content(body)
        
        with smtplib.SMTP(Config.smtp_server, 587) as server:
            server.starttls()
            server.login(Config.smtp_username, Config.smtp_psw)
            server.send_message(msg)
        logging.info("Email sent")
    except Exception as e:
        add_error(f"Email: {str(e)[:30]}")

def send_slack_message(item_title, item_price, item_url, item_image, item_size=None):
    try:
        size_text = f"\n👕 {item_size}" if item_size else ""
        message = f"*{item_title}*\n🏷️ {item_price}{size_text}\n🔗 {item_url}"
        
        response = requests.post(
            Config.slack_webhook_url, 
            json={"text": message},
            timeout=timeoutconnection
        )
        if response.status_code == 200:
            logging.info("Slack sent")
        else:
            add_error(f"Slack: {response.status_code}")
    except Exception as e:
        add_error(f"Slack: {str(e)[:30]}")

def send_telegram_message(item_title, item_price, item_url, item_image, item_size=None, thread_id=None):
    try:
        # АНТИБАН ПАУЗА 1 СЕКУНДА + защита от флуда
        telegram_antiblock.safe_delay()
        
        size_text = f"\n👕 {item_size}" if item_size else ""
        
        # Find topic name
        topic_info = ""
        if thread_id:
            for name, data in Config.topics.items():
                if data.get('thread_id') == thread_id:
                    topic_info = f"\n🏷️ {name}"
                    break
        
        message = f"<b>{item_title}</b>\n🏷️ {item_price}{size_text}{topic_info}\n🔗 {item_url}"

        # Try send to topic
        if thread_id:
            params = {
                "chat_id": Config.telegram_chat_id,
                "photo": item_image,
                "caption": message,
                "parse_mode": "HTML",
                "message_thread_id": thread_id
            }
            
            response = requests.post(
                f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto",
                data=params, 
                timeout=timeoutconnection
            )
            
            if response.status_code == 200:
                logging.info(f"✅ Sent to topic {thread_id}")
                return True
            else:
                add_error(f"TG topic: {response.status_code}", "telegram")
        
        # Fallback to main chat
        params = {
            "chat_id": Config.telegram_chat_id,
            "photo": item_image,
            "caption": message + "\n⚠️ Main chat",
            "parse_mode": "HTML",
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto",
            data=params,
            timeout=timeoutconnection
        )
        
        if response.status_code == 200:
            logging.info("✅ Sent to main chat")
            return True
        else:
            add_error(f"TG main: {response.status_code}", "telegram")
            return False

    except Exception as e:
        add_error(f"TG: {str(e)[:30]}", "telegram")
        return False

def should_exclude_item(item, exclude_catalog_ids):
    """ИСПРАВЛЕННАЯ функция фильтрации"""
    if not exclude_catalog_ids:
        return False
    
    item_catalog_id = item.get('catalog_id')
    if not item_catalog_id:
        return False
    
    item_catalog_str = str(item_catalog_id)
    exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
    
    is_excluded = item_catalog_str in exclude_list
    
    if is_excluded:
        logging.info(f"🚫 EXCLUDED: catalog_id={item_catalog_str}")
    
    return is_excluded

def scanner_loop():
    """СУПЕРБЫСТРЫЙ scanner с приоритетными топиками"""
    global bot_running
    
    while bot_running:
        try:
            logging.info("�� Starting scan cycle")
            
            # Get session with dynamic headers
            session = requests.Session()
            headers = vinted_antiblock.get_headers()
            
            # Get cookies
            session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
            cookies = session.cookies.get_dict()
            
            # Anti-block delay
            vinted_antiblock.delay()
            
            # PRIORITY SCAN: Scan priority topics more frequently
            for topic_name in PRIORITY_TOPICS:
                if not bot_running:
                    break
                    
                if topic_name in Config.topics:
                    topic_data = Config.topics[topic_name]
                    scan_topic(topic_name, topic_data, cookies, session, is_priority=True)
                    
                    # Small delay between priority topics
                    if bot_running:
                        time.sleep(random.uniform(0.2, 0.5))
            
            # NORMAL SCAN: Scan all topics including priority ones again
            for topic_name, topic_data in Config.topics.items():
                if not bot_running:
                    break
                    
                scan_topic(topic_name, topic_data, cookies, session, is_priority=(topic_name in PRIORITY_TOPICS))
                
                # Small delay between topics
                if bot_running and len(Config.topics) > 1:
                    time.sleep(random.uniform(0.3, 1.0))

            # СУПЕРБЫСТРЫЕ интервалы между циклами
            if bot_running:
                if scan_mode == "fast":
                    # Fast mode: Priority topics every 5-7s, normal every 10-15s
                    delay = random.uniform(5, 7)  # СУПЕРБЫСТРО для priority
                    logging.info(f"🐰 FAST: wait {delay:.0f}s")
                else:
                    # Slow mode: Priority topics every 15-20s, normal every 30-45s  
                    delay = random.uniform(15, 20)  # Быстрее для priority
                    logging.info(f"🐌 SLOW: wait {delay:.0f}s")
                time.sleep(delay)
                
        except Exception as e:
            add_error(f"Scanner: {str(e)[:30]}")
            logging.error(f"Error: {e}")
            if bot_running:
                time.sleep(20)

def scan_topic(topic_name, topic_data, cookies, session, is_priority=False):
    """Сканирование одного топика"""
    priority_mark = "��" if is_priority else ""
    logging.info(f"Scanning{priority_mark}: {topic_name}")
    
    params = topic_data["query"]
    exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
    thread_id = topic_data.get("thread_id")
    
    # Get new headers for each topic
    topic_headers = vinted_antiblock.get_headers()
    
    # Request with anti-blocking
    response = requests.get(
        f"{Config.vinted_url}/api/v2/catalog/items", 
        params=params, 
        cookies=cookies, 
        headers=topic_headers,
        timeout=timeoutconnection
    )

    # Handle errors
    if vinted_antiblock.handle_errors(response):
        return
    
    if response.status_code == 200:
        data = response.json()

        if data and "items" in data:
            logging.info(f"Found {len(data['items'])} items")
            
            for item in data["items"]:
                if not bot_running:
                    break
                    
                # ИСПРАВЛЕННАЯ проверка исключений
                if should_exclude_item(item, exclude_catalog_ids):
                    continue
                    
                item_id = str(item["id"])
                
                if item_id not in list_analyzed_items:
                    item_title = item["title"]
                    item_url = item["url"]
                    item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                    item_image = item["photo"]["full_size_url"]
                    item_size = item.get("size_title")

                    priority_log = "🔥 PRIORITY " if is_priority else ""
                    logging.info(f"🆕 {priority_log}NEW: {item_title} - {item_price}")

                    # Send notifications
                    if Config.smtp_username and Config.smtp_server:
                        send_email(item_title, item_price, item_url, item_image, item_size)

                    if Config.slack_webhook_url:
                        send_slack_message(item_title, item_price, item_url, item_image, item_size)

                    if Config.telegram_bot_token and Config.telegram_chat_id:
                        # АНТИБАН TELEGRAM ВКЛЮЧЕН В ФУНКЦИИ
                        success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)

                    # Save item
                    list_analyzed_items.append(item_id)
                    save_analyzed_item(item_id)
        else:
            logging.warning(f"No items: {topic_name}")
    else:
        logging.error(f"Error {response.status_code}: {topic_name}")
        add_error(f"HTTP {response.status_code}", "vinted")

# Telegram bot commands
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running, scan_mode, last_errors, telegram_errors, vinted_errors
    status = "🟢 Running" if bot_running else "�� Stopped"
    items_count = len(list_analyzed_items)
    
    mode_emoji = "🐰" if scan_mode == "fast" else "🐌"
    if scan_mode == "fast":
        mode_interval = "5-7s priority, 10-15s normal"
    else:
        mode_interval = "15-20s priority, 30-45s normal"
    mode_info = f"\n{mode_emoji} Mode: {scan_mode} ({mode_interval})"
    
    anti_info = f"\n🛡️ Vinted requests: {vinted_antiblock.request_count}"
    anti_info += f"\n📱 Telegram messages: {telegram_antiblock.message_count}"
    anti_info += f"\n🔥 Priority: {', '.join(PRIORITY_TOPICS)}"
    
    # Formatted error info
    error_info = ""
    if telegram_errors:
        tg_count = len(telegram_errors)
        tg_last = telegram_errors[-1] if telegram_errors else "N/A"
        error_info += f"\n📱 Telegram ({tg_count})({tg_last})"
        
    if vinted_errors:
        vinted_count = len(vinted_errors)
        vinted_last = vinted_errors[-1] if vinted_errors else "N/A"
        error_info += f"\n🌐 Vinted ({vinted_count})({vinted_last})"
    
    if last_errors:
        error_info += f"\n❌ Recent:\n" + "\n".join(last_errors[-2:])
    
    response = f"{status}\n📊 Items: {items_count}{mode_info}{anti_info}{error_info}"
    await update.message.reply_text(response)

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ИСПРАВЛЕННАЯ команда /log"""
    try:
        if not os.path.exists("vinted_scanner.log"):
            await update.message.reply_text("📝 Лог файл не найден")
            return
            
        with open("vinted_scanner.log", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        if not lines:
            await update.message.reply_text("📝 Лог файл пуст")
            return
            
        last_lines = lines[-8:] if len(lines) >= 8 else lines
        log_text = "".join(last_lines)
        
        if len(log_text) > 3500:
            log_text = log_text[-3500:]
            log_text = "...\n" + log_text[log_text.find('\n')+1:]
        
        await update.message.reply_text(f"📝 Последние строки:\n```\n{log_text}\n```", parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка чтения: {str(e)[:100]}")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running, scanner_thread, list_analyzed_items
    await update.message.reply_text("🔄 Restarting...")
    
    bot_running = False
    if scanner_thread:
        scanner_thread.join(timeout=5)
    
    list_analyzed_items.clear()
    try:
        with open("vinted_items.txt", "w") as f:
            f.write("")
    except:
        pass
    
    await asyncio.sleep(1)
    
    bot_running = True
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    
    await update.message.reply_text("✅ Restarted!")

async def fast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scan_mode
    scan_mode = "fast"
    await update.message.reply_text("🐰 FAST mode: 5-7s priority, 10-15s normal")

async def slow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scan_mode
    scan_mode = "slow"
    await update.message.reply_text("🐌 SLOW mode: 15-20s priority, 30-45s normal")

def signal_handler(signum, frame):
    global bot_running
    logging.info("Shutdown signal received")
    bot_running = False
    sys.exit(0)

async def setup_bot():
    application = Application.builder().token(Config.telegram_bot_token).build()
    
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("fast", fast_command))
    application.add_handler(CommandHandler("slow", slow_command))
    
    return application

def main():
    global bot_running, scanner_thread
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    load_analyzed_item()
    
    logging.info("🚀 SUPERFAST Vinted Scanner with Priority Topics & Telegram AntiBlock!")
    
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
            logging.info("Stopped by user")
        except Exception as e:
            logging.error(f"Bot error: {e}")
            try:
                while bot_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        try:
            while bot_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
