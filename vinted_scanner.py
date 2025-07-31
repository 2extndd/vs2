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
vinted_521_count = 0  # Счетчик ошибок 521

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
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.blocked_count = 0

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
        """Адаптивные задержки между запросами"""
        self.request_count += 1
        
        # Базовая задержка
        base_delay = random.uniform(0.5, 2.0)
        
        # Адаптивная задержка на основе ошибок
        if self.error_count > self.success_count:
            base_delay *= 1.5  # Увеличиваем при ошибках
        
        # Дополнительная задержка каждые 10 запросов
        if self.request_count % 10 == 0:
            base_delay += random.uniform(2, 5)
        
        # Экстренная задержка при блокировке
        if self.blocked_count > 0:
            base_delay += random.uniform(3, 8)
        
        time.sleep(base_delay)
        return base_delay

    def handle_errors(self, response):
        """Улучшенная обработка ошибок HTTP"""
        if response.status_code == 429:
            self.blocked_count += 1
            wait = random.uniform(60, 120)
            logging.warning(f"🚫 Rate limit! Блокировок: {self.blocked_count}, ждем {wait:.0f}s")
            time.sleep(wait)
            return True
        elif response.status_code in [403, 503]:
            self.blocked_count += 1
            wait = random.uniform(30, 60)
            logging.warning(f"🚫 Blocked! Блокировок: {self.blocked_count}, ждем {wait:.0f}s")
            time.sleep(wait)
            return True
        elif response.status_code == 521:
            global vinted_521_count
            vinted_521_count += 1
            
            # Увеличиваем время ожидания с каждой ошибкой
            if vinted_521_count <= 3:
                wait = random.uniform(120, 300)  # 2-5 минут
            elif vinted_521_count <= 5:
                wait = random.uniform(300, 600)  # 5-10 минут
            else:
                wait = random.uniform(600, 1200)  # 10-20 минут
            
            logging.error(f"❌ Vinted сервер недоступен (521)! Ошибка #{vinted_521_count}, ждем {wait:.0f} секунд")
            time.sleep(wait)
            return True
        elif response.status_code in [500, 502, 504]:
            wait = random.uniform(60, 180)  # 1-3 minutes for server errors
            logging.warning(f"Server error {response.status_code}! Wait {wait:.0f}s")
            time.sleep(wait)
            return True
        return False

# ANTI-BLOCKING SYSTEM FOR TELEGRAM
class TelegramAntiBlock:
    def __init__(self):
        self.message_count = 0
        self.last_message_time = 0
        self.success_count = 0
        self.error_count = 0
        self.rate_limited = 0
        
    def safe_delay(self):
        """Адаптивная защита от флуда"""
        self.message_count += 1
        current_time = time.time()
        
        # Минимальная задержка
        min_delay = 3.0
        
        # Адаптивная задержка на основе ошибок
        if self.error_count > self.success_count:
            min_delay = 5.0  # Увеличиваем при ошибках
        
        # Проверяем время с последнего сообщения
        time_since_last = current_time - self.last_message_time
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)
        
        # Дополнительная защита: каждые 10 сообщений - пауза 3-8 сек
        if self.message_count % 10 == 0:
            extra_delay = random.uniform(3, 8)
            logging.info(f"🛡️ TG Anti-flood: {extra_delay:.1f}s pause after {self.message_count} messages")
            time.sleep(extra_delay)
        
        self.last_message_time = time.time()
        return min_delay

# Global instances
vinted_antiblock = VintedAntiBlock()
telegram_antiblock = TelegramAntiBlock()

# Импорт новой антибан системы
try:
    from antiban import antiban_system
    ADVANCED_ANTIBAN = True
    logging.info("🚀 Продвинутая антибан система загружена")
except ImportError:
    ADVANCED_ANTIBAN = False
    logging.warning("⚠️ Продвинутая антибан система недоступна, используется базовая")

# Reservation System
class VintedReservation:
    def __init__(self):
        self.reserved_items = {}  # {item_id: {"url": "", "reserved_at": timestamp, "paypal_url": ""}}
        self.session = None
        self.is_logged_in = False
        
    def login_to_vinted(self):
        """Вход в тестовый аккаунт Vinted"""
        if not Config.reservation_enabled:
            return False
            
        try:
            self.session = requests.Session()
            headers = {
                "User-Agent": Config.reservation_test_account["user_agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # Получаем страницу входа
            login_url = f"{Config.vinted_url}/login"
            response = self.session.get(login_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logging.error(f"❌ Не удалось получить страницу входа: {response.status_code}")
                return False
            
            # Здесь должна быть логика входа (CSRF токен, отправка формы)
            # Пока что используем готовые cookies если есть
            if Config.reservation_test_account["session_cookies"]:
                self.session.cookies.update(Config.reservation_test_account["session_cookies"])
                self.is_logged_in = True
                logging.info("✅ Использованы готовые cookies для входа")
                return True
            
            logging.warning("⚠️ Требуется настройка входа в аккаунт")
            return False
            
        except Exception as e:
            logging.error(f"❌ Ошибка входа в Vinted: {str(e)[:50]}")
            return False
    
    def reserve_item(self, item_url, item_title):
        """Резервирование товара через PayPal"""
        if not self.is_logged_in:
            if not self.login_to_vinted():
                return None
        
        try:
            # Получаем страницу товара
            response = self.session.get(item_url, timeout=30)
            if response.status_code != 200:
                logging.error(f"❌ Не удалось получить страницу товара: {response.status_code}")
                return None
            
            # Извлекаем item_id из URL
            item_id = item_url.split('/')[-1]
            
            # Проверяем, не забронирован ли уже товар
            if item_id in self.reserved_items:
                existing = self.reserved_items[item_id]
                time_passed = time.time() - existing["reserved_at"]
                if time_passed < Config.reservation_timeout:
                    remaining = Config.reservation_timeout - time_passed
                    logging.info(f"⚠️ Товар уже забронирован на {remaining:.0f} секунд")
                    return existing["paypal_url"]
            
            # Проверяем лимит резервирований
            active_reservations = len([r for r in self.reserved_items.values() 
                                     if time.time() - r["reserved_at"] < Config.reservation_timeout])
            
            if active_reservations >= Config.reservation_max_items:
                logging.warning(f"⚠️ Достигнут лимит резервирований ({Config.reservation_max_items})")
                return None
            
            # Здесь должна быть логика резервирования через PayPal
            # Пока что создаем заглушку
            paypal_url = f"{Config.vinted_url}/checkout/{item_id}/paypal"
            
            # Сохраняем информацию о резервировании
            self.reserved_items[item_id] = {
                "url": item_url,
                "title": item_title,
                "reserved_at": time.time(),
                "paypal_url": paypal_url
            }
            
            logging.info(f"✅ Товар забронирован: {item_title}")
            return paypal_url
            
        except Exception as e:
            logging.error(f"❌ Ошибка резервирования товара: {str(e)[:50]}")
            return None
    
    def get_reservation_status(self, item_id):
        """Получить статус резервирования товара"""
        if item_id not in self.reserved_items:
            return None
        
        reservation = self.reserved_items[item_id]
        time_passed = time.time() - reservation["reserved_at"]
        
        if time_passed >= Config.reservation_timeout:
            # Удаляем истекшее резервирование
            del self.reserved_items[item_id]
            return None
        
        return {
            "remaining_time": Config.reservation_timeout - time_passed,
            "paypal_url": reservation["paypal_url"],
            "title": reservation["title"]
        }
    
    def cleanup_expired_reservations(self):
        """Очистка истекших резервирований"""
        current_time = time.time()
        expired_items = []
        
        for item_id, reservation in self.reserved_items.items():
            if current_time - reservation["reserved_at"] >= Config.reservation_timeout:
                expired_items.append(item_id)
        
        for item_id in expired_items:
            del self.reserved_items[item_id]
            logging.info(f"🗑️ Удалено истекшее резервирование: {item_id}")
        
        return len(expired_items)

# Global reservation instance
reservation_system = VintedReservation()

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
        # Адаптивная защита от флуда
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
                telegram_antiblock.success_count += 1
                logging.info(f"✅ Sent to topic {thread_id}")
                return True
            else:
                telegram_antiblock.error_count += 1
                # Обработка 429 (Too Many Requests)
                if response.status_code == 429:
                    telegram_antiblock.rate_limited += 1
                    retry_after = response.json().get("parameters", {}).get("retry_after", 30)
                    logging.warning(f"🚫 TG Rate limit! Rate limits: {telegram_antiblock.rate_limited}, waiting {retry_after}s")
                    time.sleep(retry_after + 2)  # +2 сек запас
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
            telegram_antiblock.success_count += 1
            logging.info("✅ Sent to main chat")
            return True
        else:
            telegram_antiblock.error_count += 1
            # Обработка 429 (Too Many Requests)
            if response.status_code == 429:
                telegram_antiblock.rate_limited += 1
                retry_after = response.json().get("parameters", {}).get("retry_after", 30)
                logging.warning(f"🚫 TG Rate limit! Rate limits: {telegram_antiblock.rate_limited}, waiting {retry_after}s")
                time.sleep(retry_after + 2)  # +2 сек запас
            add_error(f"TG main: {response.status_code}", "telegram")
            return False

    except Exception as e:
        add_error(f"TG: {str(e)[:30]}", "telegram")
        return False

def should_exclude_item(item, exclude_catalog_ids, topic_name=""):
    """Проверка исключения товара по catalog_id"""
    if not exclude_catalog_ids:
        return False
    
    item_catalog_id = item.get('catalog_id')
    if not item_catalog_id:
        return False
    
    item_catalog_str = str(item_catalog_id)
    exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
    
    is_excluded = item_catalog_str in exclude_list
    
    if is_excluded:
        logging.info(f"🚫 EXCLUDED [{topic_name}]: catalog_id={item_catalog_str}")
    
    return is_excluded

def scanner_loop():
    """Основной цикл сканирования"""
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
            # Очистка истекших резервирований
            if Config.reservation_enabled:
                expired_count = reservation_system.cleanup_expired_reservations()
                if expired_count > 0:
                    logging.info(f"🗑️ Очищено {expired_count} истекших резервирований")
            
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
    
    params = topic_data["query"].copy()  # Копируем параметры
    exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
    thread_id = topic_data.get("thread_id")
    
    # Исключаем catalog_ids из запроса, если они конфликтуют
    if exclude_catalog_ids and params.get("catalog_ids"):
        query_catalog_ids = params["catalog_ids"]
        exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
        query_list = [id.strip() for id in query_catalog_ids.split(',') if id.strip()]
        
        # Убираем исключаемые ID из запроса
        filtered_query_list = [id for id in query_list if id not in exclude_list]
        
        if filtered_query_list != query_list:
            removed_ids = set(query_list) - set(filtered_query_list)
            logging.info(f"🔧 [{topic_name}] Убрал из запроса: {removed_ids}")
            params["catalog_ids"] = ','.join(filtered_query_list)
    
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
        # Сбрасываем счетчик ошибок 521 при успешном запросе
        global vinted_521_count
        if vinted_521_count > 0:
            logging.info(f"✅ Vinted снова доступен! Сбрасываем счетчик ошибок 521")
            vinted_521_count = 0
        
        # Отслеживаем успешные запросы
        vinted_antiblock.success_count += 1
        
        data = response.json()

        if data and "items" in data:
            logging.info(f"Found {len(data['items'])} items for {topic_name}")
            
            for item in data["items"]:
                if not bot_running:
                    break
                    
                # Проверка исключений
                if should_exclude_item(item, exclude_catalog_ids, topic_name):
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
                        success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)

                    # Save item
                    list_analyzed_items.append(item_id)
                    save_analyzed_item(item_id)
        else:
            logging.warning(f"No items: {topic_name}")
    else:
        # Отслеживаем ошибки
        vinted_antiblock.error_count += 1
        
        if response.status_code == 521:
            logging.error(f"❌ Vinted сервер недоступен (521) для топика: {topic_name}")
            add_error(f"HTTP 521 - сервер недоступен", "vinted")
        else:
            logging.error(f"Ошибка {response.status_code}: {topic_name}")
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
    anti_info += f"\n🌐 Vinted success/errors: {vinted_antiblock.success_count}/{vinted_antiblock.error_count}"
    anti_info += f"\n🚫 Vinted blocks: {vinted_antiblock.blocked_count}"
    
    # Добавляем статистику продвинутой антибан системы
    if ADVANCED_ANTIBAN:
        try:
            advanced_stats = antiban_system.get_stats()
            anti_info += f"\n🚀 Advanced AntiBan:"
            anti_info += f"\n   📊 Total requests: {advanced_stats['total_requests']}"
            anti_info += f"\n   ❌ Total errors: {advanced_stats['total_errors']}"
            anti_info += f"\n   🚫 Total blocks: {advanced_stats['total_blocks']}"
            anti_info += f"\n   📈 Success rate: {advanced_stats['success_rate']:.1f}%"
            anti_info += f"\n   🔄 Session: {advanced_stats['current_session']}/{advanced_stats['sessions_count']}"
        except Exception as e:
            anti_info += f"\n🚀 Advanced AntiBan: ERROR - {str(e)[:30]}"
    
    anti_info += f"\n📱 Telegram messages: {telegram_antiblock.message_count}"
    anti_info += f"\n📱 TG success/errors: {telegram_antiblock.success_count}/{telegram_antiblock.error_count}"
    anti_info += f"\n🚫 TG rate limits: {telegram_antiblock.rate_limited}"
    anti_info += f"\n🔥 Priority: {', '.join(PRIORITY_TOPICS)}"
    if vinted_521_count > 0:
        anti_info += f"\n⚠️ 521 errors: {vinted_521_count}"
    
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

async def threadid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """РАБОЧАЯ команда /threadid с принудительным обновлением"""
    message = update.message
    
    if message.is_topic_message and message.message_thread_id:
        thread_id = message.message_thread_id
        
        # Найти топик
        topic_name = "Неизвестный"
        topic_data = None
        for name, data in Config.topics.items():
            if data.get('thread_id') == thread_id:
                topic_name = name
                topic_data = data
                break
        
        await update.message.reply_text(f"🧵 Thread ID: {thread_id}\n📍 Топик: {topic_name}\n🔄 Принудительное обновление...")
        
        if topic_data:
            try:
                # Получаем товары
                headers = vinted_antiblock.get_headers()
                session = requests.Session()
                session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
                cookies = session.cookies.get_dict()
                
                params = topic_data["query"]
                exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
                
                response = requests.get(f"{Config.vinted_url}/api/v2/catalog/items", 
                                      params=params, cookies=cookies, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and "items" in data:
                        sent_count = 0
                        
                        # Обрабатываем товары
                        for item in data["items"]:
                            if not should_exclude_item(item, exclude_catalog_ids):
                                item_id = str(item["id"])
                                
                                # Убираем из списка для повторной отправки
                                if item_id in list_analyzed_items:
                                    list_analyzed_items.remove(item_id)
                                
                                # Отправляем заново
                                item_title = item["title"]
                                item_url = item["url"]
                                item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                                item_image = item["photo"]["full_size_url"]
                                item_size = item.get("size_title")
                                
                                success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
                                if success:
                                    sent_count += 1
                                    # ПАУЗА 3 СЕКУНДЫ между сообщениями (anti-blocking)
                                    time.sleep(3)
                                
                                list_analyzed_items.append(item_id)
                                save_analyzed_item(item_id)
                        
                        await update.message.reply_text(f"✅ Готово! Отправлено {sent_count} товаров для топика {topic_name}")
                    else:
                        await update.message.reply_text(f"❌ Нет товаров в API для топика {topic_name}")
                else:
                    await update.message.reply_text(f"❌ Ошибка API: {response.status_code}")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Топик не найден в конфигурации")
    else:
        await update.message.reply_text("❌ Команда работает только в топиках!")

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
    """Handle /slow command - set slow scanning mode (120 seconds)"""
    global scan_mode
    scan_mode = "slow"
    await update.message.reply_text("🐌 Режим изменен на МЕДЛЕННЫЙ\n⏱️ Интервал сканирования: 120 секунд")
    logging.info("Scan mode changed to SLOW (120 seconds)")
async def chatinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chatinfo command - chat diagnostics"""
    try:
        chat = update.effective_chat
        bot = context.bot
        
        # Get full chat info
        chat_full = await bot.get_chat(chat.id)
        
        info = f"🔍 <b>Диагностика чата</b>\n"
        info += f"📊 ID: <code>{chat.id}</code>\n"
        info += f"📝 Название: {chat.title or 'N/A'}\n"
        info += f"🏷️ Тип: {chat.type}\n"
        
        if hasattr(chat_full, 'member_count') and chat_full.member_count:
            info += f"👥 Участников: <b>{chat_full.member_count}</b>\n"
        
        if hasattr(chat_full, 'is_forum'):
            info += f"🧵 Форум: {'✅ Да' if chat_full.is_forum else '❌ Нет'}\n"
        
        await update.message.reply_text(info, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка диагностики: {e}")

async def vinted_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса Vinted API"""
    try:
        await update.message.reply_text("🔍 Проверяю статус Vinted API...")
        
        headers = vinted_antiblock.get_headers()
        session = requests.Session()
        
        # Проверяем основной сайт
        try:
            response = session.get(Config.vinted_url, headers=headers, timeout=10)
            main_status = f"✅ Доступен ({response.status_code})" if response.status_code == 200 else f"❌ Ошибка ({response.status_code})"
        except Exception as e:
            main_status = f"❌ Ошибка подключения: {str(e)[:50]}"
        
        # Проверяем API
        try:
            test_params = {'page': '1', 'per_page': '1'}
            response = session.get(f"{Config.vinted_url}/api/v2/catalog/items", 
                                  params=test_params, headers=headers, timeout=10)
            api_status = f"✅ Работает ({response.status_code})" if response.status_code == 200 else f"❌ Ошибка ({response.status_code})"
        except Exception as e:
            api_status = f"❌ Ошибка API: {str(e)[:50]}"
        
        status_msg = f"🌐 <b>Статус Vinted</b>\n"
        status_msg += f"📱 Основной сайт: {main_status}\n"
        status_msg += f"🔗 API: {api_status}\n"
        status_msg += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        
        await update.message.reply_text(status_msg, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки: {str(e)[:100]}")

async def debug_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладка фильтрации - показывает конфликты между include и exclude"""
    try:
        debug_msg = "🔍 <b>Отладка фильтрации</b>\n\n"
        
        for topic_name, topic_data in Config.topics.items():
            query_catalog_ids = topic_data["query"].get("catalog_ids", "")
            exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
            
            if query_catalog_ids and exclude_catalog_ids:
                # Проверяем конфликты
                query_list = [id.strip() for id in query_catalog_ids.split(',') if id.strip()]
                exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
                
                conflicts = [id for id in exclude_list if id in query_list]
                
                if conflicts:
                    debug_msg += f"⚠️ <b>{topic_name}</b>\n"
                    debug_msg += f"📥 Include: {query_catalog_ids}\n"
                    debug_msg += f"📤 Exclude: {exclude_catalog_ids}\n"
                    debug_msg += f"🚫 Конфликты: {', '.join(conflicts)}\n\n"
                else:
                    debug_msg += f"✅ <b>{topic_name}</b> - без конфликтов\n\n"
            else:
                debug_msg += f"ℹ️ <b>{topic_name}</b> - нет фильтров\n\n"
        
        await update.message.reply_text(debug_msg, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отладки: {str(e)[:100]}")

async def reserve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Резервирование товара по команде /reserve <item_url>"""
    try:
        if not context.args:
            await update.message.reply_text("❌ Укажите ссылку на товар: /reserve <ссылка>")
            return
        
        item_url = context.args[0]
        
        # Проверяем, что это ссылка на Vinted
        if not item_url.startswith(Config.vinted_url):
            await update.message.reply_text("❌ Это не ссылка на Vinted!")
            return
        
        await update.message.reply_text("🔄 Резервирую товар...")
        
        # Извлекаем item_id из URL
        item_id = item_url.split('/')[-1]
        
        # Проверяем текущий статус
        status = reservation_system.get_reservation_status(item_id)
        if status:
            remaining_minutes = int(status["remaining_time"] // 60)
            remaining_seconds = int(status["remaining_time"] % 60)
            await update.message.reply_text(
                f"⚠️ Товар уже забронирован!\n"
                f"⏰ Осталось: {remaining_minutes}:{remaining_seconds:02d}\n"
                f"🔗 PayPal: {status['paypal_url']}"
            )
            return
        
        # Резервируем товар
        paypal_url = reservation_system.reserve_item(item_url, "Товар")
        
        if paypal_url:
            await update.message.reply_text(
                f"✅ Товар забронирован на 15 минут!\n"
                f"🔗 PayPal: {paypal_url}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Запускаем отсчет времени
            asyncio.create_task(reservation_countdown(item_id, item_url, update.message.chat_id))
        else:
            await update.message.reply_text("❌ Не удалось забронировать товар")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка резервирования: {str(e)[:100]}")

async def reservation_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус всех резервирований"""
    try:
        if not reservation_system.reserved_items:
            await update.message.reply_text("📋 Нет активных резервирований")
            return
        
        status_msg = "📋 <b>Активные резервирования:</b>\n\n"
        
        for item_id, reservation in reservation_system.reserved_items.items():
            time_passed = time.time() - reservation["reserved_at"]
            remaining_time = Config.reservation_timeout - time_passed
            
            if remaining_time > 0:
                remaining_minutes = int(remaining_time // 60)
                remaining_seconds = int(remaining_time % 60)
                status_msg += f"🕐 {reservation['title']}\n"
                status_msg += f"⏰ Осталось: {remaining_minutes}:{remaining_seconds:02d}\n"
                status_msg += f"🔗 PayPal: {reservation['paypal_url']}\n\n"
        
        await update.message.reply_text(status_msg, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статуса: {str(e)[:100]}")

async def reservation_countdown(item_id, item_url, chat_id):
    """Отсчет времени резервирования с реалтайм обновлениями"""
    try:
        # Получаем bot из глобального контекста
        from telegram.ext import Application
        app = Application.get_current()
        bot = app.bot
        
        # Отправляем начальное сообщение
        message = await bot.send_message(
            chat_id=chat_id,
            text=f"⏰ <b>Отсчет резервирования</b>\n"
                 f"🔗 Товар: {item_url}\n"
                 f"⏱️ Осталось: 15:00",
            parse_mode="HTML"
        )
        
        while True:
            await asyncio.sleep(30)  # Обновляем каждые 30 секунд
            
            # Проверяем статус резервирования
            status = reservation_system.get_reservation_status(item_id)
            if not status:
                # Резервирование истекло
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message.message_id,
                    text=f"⏰ <b>Резервирование истекло!</b>\n"
                         f"🔗 Товар: {item_url}\n"
                         f"⏱️ Время: {datetime.now().strftime('%H:%M:%S')}",
                    parse_mode="HTML"
                )
                break
            
            # Обновляем сообщение с оставшимся временем
            remaining_minutes = int(status["remaining_time"] // 60)
            remaining_seconds = int(status["remaining_time"] % 60)
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=f"⏰ <b>Отсчет резервирования</b>\n"
                     f"🔗 Товар: {item_url}\n"
                     f"⏱️ Осталось: {remaining_minutes}:{remaining_seconds:02d}",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logging.error(f"❌ Ошибка отсчета времени: {str(e)[:50]}")

async def reply_reserve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Резервирование товара по reply на сообщение с товаром"""
    try:
        # Проверяем, что это reply на сообщение
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Ответьте на сообщение с товаром командой /reserve")
            return
        
        # Ищем ссылку на Vinted в исходном сообщении
        original_text = update.message.reply_to_message.text
        vinted_links = []
        
        # Простая проверка на ссылки Vinted
        words = original_text.split()
        for word in words:
            if word.startswith(Config.vinted_url):
                vinted_links.append(word)
        
        if not vinted_links:
            await update.message.reply_text("❌ В сообщении нет ссылки на Vinted")
            return
        
        item_url = vinted_links[0]
        await update.message.reply_text("🔄 Резервирую товар...")
        
        # Извлекаем item_id из URL
        item_id = item_url.split('/')[-1]
        
        # Проверяем текущий статус
        status = reservation_system.get_reservation_status(item_id)
        if status:
            remaining_minutes = int(status["remaining_time"] // 60)
            remaining_seconds = int(status["remaining_time"] % 60)
            await update.message.reply_text(
                f"⚠️ Товар уже забронирован!\n"
                f"⏰ Осталось: {remaining_minutes}:{remaining_seconds:02d}\n"
                f"🔗 PayPal: {status['paypal_url']}"
            )
            return
        
        # Резервируем товар
        paypal_url = reservation_system.reserve_item(item_url, "Товар")
        
        if paypal_url:
            await update.message.reply_text(
                f"✅ Товар забронирован на 15 минут!\n"
                f"🔗 PayPal: {paypal_url}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Запускаем отсчет времени
            asyncio.create_task(reservation_countdown(item_id, item_url, update.message.chat_id))
        else:
            await update.message.reply_text("❌ Не удалось забронировать товар")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка резервирования: {str(e)[:100]}")

async def unified_reserve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Унифицированная команда резервирования"""
    try:
        # Если есть аргументы - используем их как ссылку
        if context.args:
            item_url = context.args[0]
        # Если это reply на сообщение - извлекаем ссылку из него
        elif update.message.reply_to_message:
            original_text = update.message.reply_to_message.text
            vinted_links = []
            words = original_text.split()
            for word in words:
                if word.startswith(Config.vinted_url):
                    vinted_links.append(word)
            
            if not vinted_links:
                await update.message.reply_text("❌ В сообщении нет ссылки на Vinted")
                return
            
            item_url = vinted_links[0]
        else:
            await update.message.reply_text("❌ Укажите ссылку или ответьте на сообщение с товаром: /reserve <ссылка>")
            return
        
        # Проверяем, что это ссылка на Vinted
        if not item_url.startswith(Config.vinted_url):
            await update.message.reply_text("❌ Это не ссылка на Vinted!")
            return
        
        await update.message.reply_text("🔄 Резервирую товар...")
        
        # Извлекаем item_id из URL
        item_id = item_url.split('/')[-1]
        
        # Проверяем текущий статус
        status = reservation_system.get_reservation_status(item_id)
        if status:
            remaining_minutes = int(status["remaining_time"] // 60)
            remaining_seconds = int(status["remaining_time"] % 60)
            await update.message.reply_text(
                f"⚠️ Товар уже забронирован!\n"
                f"⏰ Осталось: {remaining_minutes}:{remaining_seconds:02d}\n"
                f"🔗 PayPal: {status['paypal_url']}"
            )
            return
        
        # Резервируем товар
        paypal_url = reservation_system.reserve_item(item_url, "Товар")
        
        if paypal_url:
            await update.message.reply_text(
                f"✅ Товар забронирован на 15 минут!\n"
                f"🔗 PayPal: {paypal_url}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Запускаем отсчет времени
            asyncio.create_task(reservation_countdown(item_id, item_url, update.message.chat_id))
        else:
            await update.message.reply_text("❌ Не удалось забронировать товар")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка резервирования: {str(e)[:100]}")



def signal_handler(signum, frame):
    global bot_running
    logging.info("Shutdown signal received")
    bot_running = False
    sys.exit(0)

async def setup_bot():
    application = Application.builder().token(Config.telegram_bot_token).build()
    
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("threadid", threadid_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("fast", fast_command))
    application.add_handler(CommandHandler("slow", slow_command))
    application.add_handler(CommandHandler("chatinfo", chatinfo_command))
    application.add_handler(CommandHandler("vinted", vinted_status_command))
    application.add_handler(CommandHandler("debug", debug_filter_command))
    application.add_handler(CommandHandler("reserve", unified_reserve_command))
    application.add_handler(CommandHandler("reservations", reservation_status_command))    
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
                    time.sleep(2)  # ANTI-BLOCKING
            except KeyboardInterrupt:
                pass
    else:
        try:
            while bot_running:
                time.sleep(2)  # ANTI-BLOCKING
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
