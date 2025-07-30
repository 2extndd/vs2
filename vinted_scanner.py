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
import re
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
    """Handle /threadid command - get real thread IDs from supergroup topics"""
    await update.message.reply_text("🔍 Ищу реальные thread_id топиков в супергруппе...")
    
    try:
        # Получаем информацию о чате
        bot = Bot(token=Config.telegram_bot_token)
        chat = await bot.get_chat(chat_id=Config.telegram_chat_id)
        
        if not getattr(chat, 'is_forum', False):
            await update.message.reply_text("❌ Группа не настроена как форум! Включите Topics в настройках группы.")
            return
        
        # Попробуем найти рабочие thread_id
        working_threads = []
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        
        await update.message.reply_text("🧪 Тестирую thread_id от 1 до 100...")
        
        for test_id in range(1, 101):
            params = {
                "chat_id": Config.telegram_chat_id,
                "text": f"🔍 Поиск thread_id: {test_id}",
                "message_thread_id": test_id
            }
            
            response = requests.post(url, data=params, timeout=10)
            
            if response.status_code == 200:
                working_threads.append(test_id)
                await update.message.reply_text(f"✅ Найден рабочий thread_id: {test_id}")
            
            # Задержка чтобы избежать rate limit
            import asyncio
            await asyncio.sleep(0.2)
        
        # Показываем результаты
        if working_threads:
            result = f"🎯 Найдены рабочие thread_id: {', '.join(map(str, working_threads))}\n\n"
            result += "📝 Для обновления Config.py:\n"
            
            topic_names = list(Config.topics.keys())
            for i, thread_id in enumerate(working_threads):
                if i < len(topic_names):
                    result += f"'{topic_names[i]}': {{'thread_id': {thread_id}, ...}}\n"
                else:
                    result += f"'new_topic_{i+1}': {{'thread_id': {thread_id}, ...}}\n"
            
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("❌ Не найдено рабочих thread_id!\nВозможно, топики не созданы в группе.")
        
        # Показываем текущую конфигурацию
        config_info = "\n📋 Текущая конфигурация:\n"
        for topic_name, topic_data in list(Config.topics.items())[:5]:
            config_info += f"• {topic_name}: {topic_data['thread_id']}\n"
        
        await update.message.reply_text(config_info)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

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

async def get_real_threads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getthreads command - get real forum topic IDs"""
    await update.message.reply_text("🔍 Получаю список реальных топиков форума...")
    
    try:
        bot = Bot(token=Config.telegram_bot_token)
        
        # Method to get forum topics (if available in python-telegram-bot)
        try:
            # Try to get forum topics using getForumTopicIconStickers
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/getForumTopicIconStickers"
            response = requests.get(url)
            
            if response.status_code == 200:
                await update.message.reply_text("✅ API доступен для работы с форумами")
            else:
                await update.message.reply_text(f"⚠️ Forum API response: {response.status_code}")
        except Exception as e:
            await update.message.reply_text(f"Forum API error: {e}")
        
        # Alternative method: try to send a test message to various thread IDs
        await update.message.reply_text("🧪 Тестирую диапазон thread_id от 1 до 20...")
        
        working_threads = []
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        
        for test_id in range(1, 21):
            params = {
                "chat_id": Config.telegram_chat_id,
                "text": f"🧪 Test thread {test_id}",
                "message_thread_id": test_id
            }
            
            response = requests.post(url, data=params, timeout=10)
            
            if response.status_code == 200:
                working_threads.append(test_id)
                await update.message.reply_text(f"✅ Thread {test_id} работает!")
            
            # Small delay to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)
        
        if working_threads:
            result = f"✅ Найдены рабочие thread_id: {', '.join(map(str, working_threads))}"
        else:
            result = "❌ Не найдено рабочих thread_id в диапазоне 1-20"
            
        await update.message.reply_text(result)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

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

async def test_web_thread_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /testwebthread command - test thread from web URL"""
    args = context.args
    
    if not args:
        await update.message.reply_text("❌ Укажите thread_id из веб-ссылки\nПример: /testwebthread 718")
        return
    
    try:
        web_thread_id = int(args[0])
        await update.message.reply_text(f"🧪 Тестирую thread_id {web_thread_id} из веб-ссылки...")
        
        # Test the exact thread_id from web URL
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        params = {
            "chat_id": Config.telegram_chat_id,
            "text": f"🧪 Тест веб thread_id {web_thread_id}",
            "message_thread_id": web_thread_id
        }
        
        response = requests.post(url, data=params, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Thread {web_thread_id} работает!")
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_desc = error_data.get('description', 'Unknown error')
            await update.message.reply_text(f"❌ Thread {web_thread_id} не работает\nОшибка: {error_desc}")
            
            # Try some variations
            variations = [web_thread_id + 1, web_thread_id - 1, web_thread_id + 100, web_thread_id - 100]
            await update.message.reply_text(f"🔄 Пробую варианты: {variations}")
            
            for var_id in variations:
                params["message_thread_id"] = var_id
                params["text"] = f"🧪 Вариант {var_id}"
                
                var_response = requests.post(url, data=params, timeout=30)
                if var_response.status_code == 200:
                    await update.message.reply_text(f"✅ Вариант {var_id} работает!")
                    break
                    
    except ValueError:
        await update.message.reply_text("❌ Некорректный thread_id")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def get_real_thread_ids_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getrealth command - find and map real thread IDs to topics"""
    await update.message.reply_text("🎯 Автоматический поиск и сопоставление thread_id с топиками...")
    
    try:
        working_threads = []
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        
        # Быстрый поиск в диапазоне 1-50
        for test_id in range(1, 51):
            params = {
                "chat_id": Config.telegram_chat_id,
                "text": f"🔍 Test {test_id}",
                "message_thread_id": test_id
            }
            
            response = requests.post(url, data=params, timeout=5)
            
            if response.status_code == 200:
                working_threads.append(test_id)
            
            import asyncio
            await asyncio.sleep(0.1)
        
        if working_threads:
            await update.message.reply_text(f"✅ Найдено {len(working_threads)} рабочих thread_id: {working_threads}")
            
            # Создаем обновленную конфигурацию
            topic_names = list(Config.topics.keys())
            update_config = "🔧 Обновленная конфигурация для Config.py:\n\n"
            
            for i, topic_name in enumerate(topic_names):
                if i < len(working_threads):
                    thread_id = working_threads[i]
                    update_config += f"'{topic_name}': {{'thread_id': {thread_id}, 'query': {{...}}}},\n"
                else:
                    update_config += f"'{topic_name}': {{'thread_id': None, 'query': {{...}}}},\n"
            
            await update.message.reply_text(update_config)
            
            # Предлагаем автоматическое обновление
            if len(working_threads) >= len(topic_names):
                await update.message.reply_text("✨ Достаточно thread_id для всех топиков! Используйте /updateconfig для автоматического обновления.")
            else:
                await update.message.reply_text(f"⚠️ Найдено только {len(working_threads)} thread_id для {len(topic_names)} топиков. Создайте больше топиков в группе.")
        else:
            await update.message.reply_text("❌ Рабочие thread_id не найдены. Проверьте, что топики созданы в группе.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def update_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /updateconfig command - automatically update Config.py with found thread_id"""
    await update.message.reply_text("🔄 Автоматическое обновление Config.py...")
    
    try:
        # Сначала находим рабочие thread_id
        working_threads = []
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        
        for test_id in range(1, 31):
            params = {
                "chat_id": Config.telegram_chat_id,
                "text": f"🔄 Config update test {test_id}",
                "message_thread_id": test_id
            }
            
            response = requests.post(url, data=params, timeout=5)
            
            if response.status_code == 200:
                working_threads.append(test_id)
            
            import asyncio
            await asyncio.sleep(0.1)
        
        if not working_threads:
            await update.message.reply_text("❌ Не найдено рабочих thread_id для обновления.")
            return
        
        # Читаем текущий Config.py
        try:
            with open('Config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка чтения Config.py: {e}")
            return
        
        # Обновляем thread_id
        topic_names = list(Config.topics.keys())
        updated_content = config_content
        
        for i, topic_name in enumerate(topic_names):
            if i < len(working_threads):
                new_thread_id = working_threads[i]
                # Ищем и заменяем thread_id для каждого топика
                pattern = f'("{topic_name}":\\s*{{[^}}]*"thread_id":\\s*)[^,}}]*'
                replacement = f'\\g<1>{new_thread_id}'
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Сохраняем обновленный файл
        try:
            with open('Config.py', 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            await update.message.reply_text(f"✅ Config.py обновлен!\nИспользованы thread_id: {working_threads[:len(topic_names)]}")
            await update.message.reply_text("🔄 Перезапустите бота командой /restart для применения изменений.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка записи Config.py: {e}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    """
    Автоматически тестирует диапазон thread_id для каждого топика, находит рабочий и предлагает обновить конфиг.
    """
    await update.message.reply_text("🤖 Автоматический подбор thread_id для топиков...")
    import asyncio
    url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
    results = []
    topic_thread_map = {}
    for topic_name, topic_data in Config.topics.items():
        await update.message.reply_text(f"🔍 Тестирую топик: {topic_name}")
        found = False
        for test_id in range(1, 30):
            params = {
                "chat_id": Config.telegram_chat_id,
                "text": f"🧪 Авто-тест {topic_name} thread_id={test_id}",
                "message_thread_id": test_id
            }
            response = requests.post(url, data=params, timeout=10)
            if response.status_code == 200:
                results.append(f"✅ {topic_name}: thread_id={test_id}")
                topic_thread_map[topic_name] = test_id
                await update.message.reply_text(f"✅ Найден рабочий thread_id={test_id} для {topic_name}")
                found = True
                break
            await asyncio.sleep(0.5)
        if not found:
            results.append(f"❌ {topic_name}: не найден рабочий thread_id в диапазоне 1-30")
            await update.message.reply_text(f"❌ Не найден рабочий thread_id для {topic_name}")
    result_text = "📊 Авто-результаты:\n\n" + "\n".join(results)
    await update.message.reply_text(result_text)
    # Предложить обновить конфиг
    if topic_thread_map:
        update_text = "\n\nДля обновления Config.py скопируйте эти значения:\n"
        for topic_name, thread_id in topic_thread_map.items():
            update_text += f"'{topic_name}': {{'thread_id': {thread_id}, ...}},\n"
        await update.message.reply_text(update_text)

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
    application.add_handler(CommandHandler("getthreads", get_real_threads_command))
    application.add_handler(CommandHandler("testwebthread", test_web_thread_command))
    application.add_handler(CommandHandler("checktopics", check_topics_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("getrealth", get_real_thread_ids_command))
    application.add_handler(CommandHandler("updateconfig", update_config_command))
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
