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
system_mode = "auto"  # auto, basic, advanced, proxy, noproxy

# PRIORITY TOPICS - these scan more frequently
PRIORITY_TOPICS = ["bags", "bags 2"]

# ЗАЩИТА ОТ ДУБЛИРОВАНИЯ
last_scan_time = {}  # Время последнего сканирования каждого топика
min_scan_interval = 3  # Минимальный интервал между сканированиями одного топика (в секундах)

# ПРОДВИНУТАЯ АНТИБАН СИСТЕМА
try:
    from advanced_antiban import get_advanced_system
    advanced_system = get_advanced_system()
    ADVANCED_SYSTEM_AVAILABLE = True
    logging.info(f"🚀 Продвинутая антибан система загружена (ID: {id(advanced_system)})")
except ImportError as e:
    ADVANCED_SYSTEM_AVAILABLE = False
    logging.warning(f"⚠️ Продвинутая система недоступна: {e}")

# ТРЕХУРОВНЕВАЯ СИСТЕМА ЗАЩИТЫ
current_system = "basic"  # basic, advanced_no_proxy, advanced_proxy
basic_system_errors = 0
advanced_no_proxy_errors = 0
advanced_proxy_errors = 0
max_errors_before_switch = 2
last_switch_time = time.time()
switch_interval = 30

# СЧЕТЧИКИ ДЛЯ СТАТИСТИКИ
basic_requests = 0
basic_success = 0
advanced_no_proxy_requests = 0
advanced_no_proxy_success = 0
advanced_proxy_requests = 0
advanced_proxy_success = 0

# ПАРАМЕТРЫ ЭФФЕКТИВНОСТИ
min_success_rate_for_economy = 0.6
max_errors_for_economy = 1
economy_check_interval = 45
recovery_threshold = 15
stuck_time_threshold = 900

def should_switch_system():
    """Логика переключения трехуровневой системы"""
    global current_system, basic_system_errors, advanced_no_proxy_errors, advanced_proxy_errors
    global last_switch_time, switch_interval, min_success_rate_for_economy, max_errors_for_economy, economy_check_interval
    
    current_time = time.time()
    
    # Принудительное переключение на продвинутую систему после 4 минут
    if current_system == "basic" and current_time - last_switch_time >= 240:
        logging.info(f"🔄 ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ: basic -> advanced_no_proxy (время работы: 4 минуты)")
        current_system = "advanced_no_proxy"
        last_switch_time = current_time
        return True
    
    # Принудительное переключение с прокси на не прокси через 2 минуты
    elif current_system == "advanced_proxy" and current_time - last_switch_time >= 120:
        logging.info(f"🔄 ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ: advanced_proxy -> advanced_no_proxy (экономия прокси: 2 минуты)")
        current_system = "advanced_no_proxy"
        last_switch_time = current_time
        return True
    
    # Переключение с базовой на продвинутую без прокси
    if current_system == "basic" and basic_system_errors >= max_errors_before_switch:
        logging.info(f"🔄 ПЕРЕКЛЮЧЕНИЕ: basic -> advanced_no_proxy (ошибок: {basic_system_errors})")
        current_system = "advanced_no_proxy"
        basic_system_errors = 0
        last_switch_time = current_time
        return True
        
    # Переключение с продвинутой без прокси на продвинутую с прокси
    elif current_system == "advanced_no_proxy" and advanced_no_proxy_errors >= max_errors_before_switch:
        logging.info(f"🔄 ПЕРЕКЛЮЧЕНИЕ: advanced_no_proxy -> advanced_proxy (ошибок: {advanced_no_proxy_errors})")
        current_system = "advanced_proxy"
        advanced_no_proxy_errors = 0
        last_switch_time = current_time
        return True
        
    # Переключение обратно на продвинутую без прокси (экономия трафика)
    elif current_system == "advanced_proxy":
        # Если прокси дают много ошибок, переключаемся обратно на без прокси
        if advanced_proxy_errors >= max_errors_before_switch:
            logging.info(f"🔄 ПЕРЕКЛЮЧЕНИЕ: advanced_proxy -> advanced_no_proxy (много ошибок прокси: {advanced_proxy_errors})")
            current_system = "advanced_no_proxy"
            advanced_proxy_errors = 0
            last_switch_time = current_time
            return True
        
        # Проверка экономии ресурсов каждые 45 секунд
        if current_time - last_switch_time >= economy_check_interval:
            last_switch_time = current_time
            
            if advanced_no_proxy_requests > 0:
                success_rate = advanced_no_proxy_success / advanced_no_proxy_requests
                if success_rate >= min_success_rate_for_economy and advanced_no_proxy_errors <= max_errors_for_economy:
                    logging.info(f"🔄 ПЕРЕКЛЮЧЕНИЕ: advanced_proxy -> advanced_no_proxy (успешность: {success_rate:.1%}, ошибок: {advanced_no_proxy_errors})")
                    current_system = "advanced_no_proxy"
                    return True
            elif advanced_no_proxy_success >= 3 and advanced_no_proxy_errors <= max_errors_for_economy:
                logging.info(f"🔄 ПЕРЕКЛЮЧЕНИЕ: advanced_proxy -> advanced_no_proxy (успешных запросов: {advanced_no_proxy_success})")
                current_system = "advanced_no_proxy"
                return True
    
    return False

def update_system_stats(system_name, success=True):
    """Обновление статистики системы"""
    global basic_requests, basic_success, advanced_no_proxy_requests, advanced_no_proxy_success
    global advanced_proxy_requests, advanced_proxy_success, basic_system_errors, advanced_no_proxy_errors, advanced_proxy_errors
    
    if system_name == "basic":
        basic_requests += 1
        if success:
            basic_success += 1
            logging.info(f"✅ БАЗОВАЯ СИСТЕМА: Успешный запрос ({basic_success}/{basic_requests})")
        else:
            basic_system_errors += 1
            logging.warning(f"❌ БАЗОВАЯ СИСТЕМА: Ошибка ({basic_system_errors})")
            
    elif system_name == "advanced_no_proxy":
        advanced_no_proxy_requests += 1
        if success:
            advanced_no_proxy_success += 1
            logging.info(f"✅ ПРОДВИНУТАЯ БЕЗ ПРОКСИ: Успешный запрос ({advanced_no_proxy_success}/{advanced_no_proxy_requests})")
        else:
            advanced_no_proxy_errors += 1
            logging.warning(f"❌ ПРОДВИНУТАЯ БЕЗ ПРОКСИ: Ошибка ({advanced_no_proxy_errors})")
            
    elif system_name == "advanced_proxy":
        advanced_proxy_requests += 1
        if success:
            advanced_proxy_success += 1
            logging.info(f"✅ ПРОДВИНУТАЯ С ПРОКСИ: Успешный запрос ({advanced_proxy_success}/{advanced_proxy_requests})")
        else:
            advanced_proxy_errors += 1
            logging.warning(f"❌ ПРОДВИНУТАЯ С ПРОКСИ: Ошибка ({advanced_proxy_errors})")

# ANTI-BLOCKING SYSTEM FOR VINTED
class VintedAntiBlock:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]
        self.request_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.consecutive_errors = 0
        self.last_error_time = 0
    
    def get_headers(self):
        """Заголовки с дополнительными параметрами"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
    
    def delay(self):
        """Задержки с адаптивной логикой"""
        self.request_count += 1
        current_time = time.time()
        
        base_delay = random.uniform(0.8, 2.5)
        
        if self.consecutive_errors > 0:
            error_multiplier = min(1.5 + (self.consecutive_errors * 0.3), 3.0)
            base_delay *= error_multiplier
        
        if self.request_count % 8 == 0:
            base_delay += random.uniform(3, 8)
        
        time_since_last = current_time - self.last_error_time
        if time_since_last < 30:
            base_delay += random.uniform(2, 5)
        
        time.sleep(base_delay)
    
    def handle_errors(self, response):
        """Обработка ошибок с адаптивными задержками"""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        if response.status_code == 429:
            base_wait = 60 + (self.consecutive_errors * 15)
            wait = random.uniform(base_wait, base_wait + 60)
            logging.warning(f"Rate limit! Wait {wait:.0f}s (consecutive: {self.consecutive_errors})")
            time.sleep(wait)
            return True
        elif response.status_code in [403, 503]:
            base_wait = 30 + (self.consecutive_errors * 10)
            wait = random.uniform(base_wait, base_wait + 30)
            logging.warning(f"Blocked! Wait {wait:.0f}s (consecutive: {self.consecutive_errors})")
            time.sleep(wait)
            return True
        elif response.status_code in [500, 502, 504]:
            wait = random.uniform(10, 30)
            logging.warning(f"Server error {response.status_code}! Wait {wait:.0f}s")
            time.sleep(wait)
            return True
        else:
            self.consecutive_errors = 0
            return False
    
    def get_stats(self):
        """Получение статистики базовой системы"""
        success_rate = (self.success_count / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'success_rate': success_rate,
            'consecutive_errors': self.consecutive_errors
        }

# ANTI-BLOCKING SYSTEM FOR TELEGRAM
class TelegramAntiBlock:
    def __init__(self):
        self.message_count = 0
        self.last_message_time = 0
        self.consecutive_errors = 0
        self.last_error_time = 0
        self.error_backoff = 1  # Начальная задержка при ошибках
        
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

    def handle_telegram_error(self, error_type):
        """Обработка ошибок Telegram с экспоненциальной задержкой"""
        current_time = time.time()
        
        if error_type in ["429", "conflict", "getUpdates"]:
            self.consecutive_errors += 1
            
            # Экспоненциальная задержка: 2^errors секунд (максимум 60 секунд)
            backoff_time = min(2 ** self.consecutive_errors, 60)
            
            logging.warning(f"⚠️ TG Error {error_type}: {backoff_time}s backoff (errors: {self.consecutive_errors})")
            time.sleep(backoff_time)
            
            # Если много ошибок подряд, увеличиваем базовую задержку
            if self.consecutive_errors >= 5:
                self.error_backoff = min(self.error_backoff * 2, 10)
                logging.warning(f"🔄 TG: Увеличена базовая задержка до {self.error_backoff}s")
        else:
            # Сброс счетчика при успешных запросах
            if self.consecutive_errors > 0:
                logging.info(f"✅ TG: Сброс счетчика ошибок (было: {self.consecutive_errors})")
                self.consecutive_errors = 0
                self.error_backoff = 1

    async def safe_send_message(self, chat_id, message):
        """Безопасная отправка сообщения с антибаном и самовосстановлением"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Антибан пауза с учетом ошибок
                self.safe_delay()
                
                # Дополнительная задержка при ошибках
                if self.consecutive_errors > 0:
                    time.sleep(self.error_backoff)
                
                # Отправка сообщения через Telegram API
                response = requests.post(
                    f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    },
                    timeout=timeoutconnection
                )
                
                if response.status_code == 200:
                    logging.info(f"✅ Сообщение отправлено в {chat_id}")
                    self.handle_telegram_error("success")
                    return True
                elif response.status_code == 429:
                    self.handle_telegram_error("429")
                    if attempt < max_retries - 1:
                        continue
                else:
                    add_error(f"TG send: {response.status_code}", "telegram")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Экспоненциальная задержка
                        continue
                    return False
                    
            except requests.exceptions.RequestException as e:
                error_msg = str(e).lower()
                if "conflict" in error_msg or "getupdates" in error_msg:
                    self.handle_telegram_error("conflict")
                    if attempt < max_retries - 1:
                        continue
                else:
                    add_error(f"TG send error: {str(e)[:30]}", "telegram")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False
            except Exception as e:
                add_error(f"TG send error: {str(e)[:30]}", "telegram")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False
        
        return False

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

        # Try send to topic if thread_id is provided
        if thread_id:
            try:
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
                elif response.status_code == 400:
                    # Ошибка 400 может означать, что топики недоступны
                    logging.warning(f"⚠️ Topics not available (400 error), sending to main chat")
                    add_error(f"TG topic disabled: {response.status_code}", "telegram")
                else:
                    add_error(f"TG topic: {response.status_code}", "telegram")
                    
            except Exception as e:
                logging.error(f"❌ Error sending to topic: {e}")
                add_error(f"TG topic error: {str(e)[:30]}", "telegram")
        
        # Fallback to main chat
        main_chat_marker = "📱 MAIN CHAT" if topic_info else ""
        params = {
            "chat_id": Config.telegram_chat_id,
            "photo": item_image,
            "caption": message + (f"\n🏷️ Topic: {topic_info}" if topic_info else "") + (f"\n{main_chat_marker}" if main_chat_marker else ""),
            "parse_mode": "HTML",
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto",
            data=params,
            timeout=timeoutconnection
        )
        
        if response.status_code == 200:
            if main_chat_marker:
                logging.info("✅ Sent to main chat (with topic info)")
            else:
                logging.info("✅ Sent to main chat")
            return True
        else:
            add_error(f"TG main: {response.status_code}", "telegram")
            return False

    except Exception as e:
        add_error(f"TG: {str(e)[:30]}", "telegram")
        return False

def should_exclude_item(item, exclude_catalog_ids):
    """ИСПРАВЛЕННАЯ функция фильтрации с детальным логированием"""
    if not exclude_catalog_ids:
        logging.debug(f"🔍 No exclude_catalog_ids specified")
        return False
    
    item_catalog_id = item.get('catalog_id')
    if not item_catalog_id:
        logging.debug(f"🔍 Item has no catalog_id: {item.get('title', 'Unknown')}")
        return False
    
    item_catalog_str = str(item_catalog_id)
    exclude_list = [id.strip() for id in exclude_catalog_ids.split(',') if id.strip()]
    
    is_excluded = item_catalog_str in exclude_list
    
    if is_excluded:
        logging.info(f"🚫 EXCLUDED: catalog_id={item_catalog_str} | title={item.get('title', 'Unknown')}")
    else:
        logging.debug(f"✅ PASSED: catalog_id={item_catalog_str} | title={item.get('title', 'Unknown')} | exclude_list={exclude_list}")
    
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
                    if ADVANCED_SYSTEM_AVAILABLE and system_mode in ["auto", "advanced"]:
                        # Пробуем продвинутую систему (пока без полной интеграции)
                        logging.info(f"🚀 Продвинутая система активна для {topic_name}")
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
                    # Slow mode: Priority topics every 25-35s, normal every 45-60s  
                    delay = random.uniform(25, 35)  # Более медленно для стабильности
                    logging.info(f"🐌 SLOW: wait {delay:.0f}s")
                
                # УЛУЧШЕННАЯ СИСТЕМА ЗАДЕРЖЕК ПРИ ОШИБКАХ
                if len(last_errors) > 0:
                    # Если есть ошибки, увеличиваем задержку
                    error_delay = min(len(last_errors) * 5, 30)  # Максимум 30 секунд
                    delay += error_delay
                    logging.warning(f"⚠️ Увеличена задержка из-за ошибок: +{error_delay}s")
                
                # НОВАЯ ЛОГИКА: Автоматическое самовосстановление в каждом цикле
                auto_recovery_system()
                
                time.sleep(delay)
                
        except Exception as e:
            add_error(f"Scanner: {str(e)[:30]}")
            logging.error(f"Error: {e}")
            
            # Обработка Telegram конфликтов
            if "Conflict: terminated by other getUpdates request" in str(e):
                logging.warning("⚠️ Обнаружен конфликт Telegram ботов")
                logging.info("🔄 Ожидание 30 секунд для разрешения конфликта...")
                time.sleep(30)
            elif bot_running:
                time.sleep(20)

def scan_topic(topic_name, topic_data, cookies, session, is_priority=False):
    """Сканирование одного топика с трехуровневой системой защиты"""
    global current_system, last_scan_time
    
    # НОВАЯ ЛОГИКА: Проверка самовосстановления перед каждым сканированием
    auto_recovery_system()
    
    # Проверяем, не сканировали ли мы этот топик слишком недавно
    current_time = time.time()
    if topic_name in last_scan_time:
        time_since_last_scan = current_time - last_scan_time[topic_name]
        if time_since_last_scan < min_scan_interval:
            logging.debug(f"⏰ Skipping {topic_name} - scanned {time_since_last_scan:.1f}s ago")
            return
    
    # Обновляем время последнего сканирования
    last_scan_time[topic_name] = current_time
    
    priority_mark = "🔥" if is_priority else ""
    logging.info(f"Scanning{priority_mark}: {topic_name}")
    
    # Поддержка старой и новой структуры конфигурации
    if "query" in topic_data:
        # Старая структура
        params = topic_data["query"]
        exclude_catalog_ids = topic_data.get("exclude_catalog_ids", "")
        thread_id = topic_data.get("thread_id")
    else:
        # Новая структура
        params = {
            'page': '1',
            'per_page': '2',
            'search_text': '',
            'catalog_ids': topic_data.get('catalog_ids', ''),
            'brand_ids': topic_data.get('brand_ids', ''),
            'order': 'newest_first',
            'price_to': str(Config.price_limit),
        }
        exclude_catalog_ids = ""
        thread_id = None
    
    # Проверяем необходимость переключения системы
    if should_switch_system():
        logging.info(f"🔄 СИСТЕМА ПЕРЕКЛЮЧЕНА НА: {current_system.upper()}")
    
    data = None
    used_system = current_system
    
    # ТРЕХУРОВНЕВАЯ СИСТЕМА ЗАЩИТЫ
    if current_system == "basic":
        # БАЗОВАЯ СИСТЕМА
        logging.info(f"🛡️ [{topic_name}] Запрос через БАЗОВУЮ систему")
        
        topic_headers = vinted_antiblock.get_headers()
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{Config.vinted_url}/api/v2/catalog/items", 
                    params=params, 
                    cookies=cookies, 
                    headers=topic_headers,
                    timeout=timeoutconnection
                )

                if vinted_antiblock.handle_errors(response):
                    if attempt < max_retries - 1:
                        logging.info(f"🔄 Повторная попытка {attempt + 1}/{max_retries}")
                        time.sleep(random.uniform(2, 5))
                        continue
                    else:
                        logging.error(f"❌ Все попытки исчерпаны для {topic_name}")
                        update_system_stats("basic", success=False)
                        return
                
                if response.status_code == 200:
                    data = response.json()
                    update_system_stats("basic", success=True)
                    break
                else:
                    logging.error(f"Error {response.status_code}: {topic_name}")
                    add_error(f"HTTP {response.status_code}", "vinted")
                    update_system_stats("basic", success=False)
                    
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2, 5))
                        continue
                    else:
                        return
                        
            except Exception as e:
                logging.error(f"❌ Ошибка запроса: {e}")
                update_system_stats("basic", success=False)
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                    continue
                else:
                    add_error(f"Request error: {str(e)[:30]}", "vinted")
                    return
    
    elif current_system == "advanced_no_proxy":
        # ПРОДВИНУТАЯ СИСТЕМА БЕЗ ПРОКСИ
        if ADVANCED_SYSTEM_AVAILABLE:
            try:
                logging.info(f"🚀 [{topic_name}] Запрос через ПРОДВИНУТУЮ систему БЕЗ ПРОКСИ")
                
                # Настраиваем продвинутую систему на работу без прокси
                advanced_system.proxy_mode = "disabled"
                advanced_system.current_proxy = None
                
                url = f"{Config.vinted_url}/api/v2/catalog/items"
                data = advanced_system.make_http_request(url, params, cookies)
                
                if data and "items" in data:
                    logging.info(f"✅ ПРОДВИНУТАЯ БЕЗ ПРОКСИ: Found {len(data.get('items', []))} items for {topic_name}")
                    update_system_stats("advanced_no_proxy", success=True)
                else:
                    logging.warning(f"⚠️ Продвинутая система без прокси не вернула данные для {topic_name}")
                    update_system_stats("advanced_no_proxy", success=False)
                    
            except Exception as e:
                logging.error(f"❌ Ошибка продвинутой системы без прокси: {e}")
                update_system_stats("advanced_no_proxy", success=False)
        
        # Fallback на базовую систему (временный, не меняем current_system)
        if not data:
            logging.info(f"🛡️ [{topic_name}] ВРЕМЕННЫЙ fallback на БАЗОВУЮ систему")
            
            topic_headers = vinted_antiblock.get_headers()
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        f"{Config.vinted_url}/api/v2/catalog/items", 
                        params=params, 
                        cookies=cookies, 
                        headers=topic_headers,
                        timeout=timeoutconnection
                    )

                    if vinted_antiblock.handle_errors(response):
                        if attempt < max_retries - 1:
                            logging.info(f"🔄 Повторная попытка {attempt + 1}/{max_retries}")
                            time.sleep(random.uniform(2, 5))
                            continue
                        else:
                            logging.error(f"❌ Все попытки исчерпаны для {topic_name}")
                            return
                    
                    if response.status_code == 200:
                        data = response.json()
                        logging.info(f"✅ ВРЕМЕННЫЙ FALLBACK: Успешный запрос через базовую систему")
                        break
                    else:
                        logging.error(f"Error {response.status_code}: {topic_name}")
                        add_error(f"HTTP {response.status_code}", "vinted")
                        
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(2, 5))
                            continue
                        else:
                            return
                            
                except Exception as e:
                    logging.error(f"❌ Ошибка запроса: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2, 5))
                        continue
                    else:
                        add_error(f"Request error: {str(e)[:30]}", "vinted")
                        return
    
    elif current_system == "advanced_proxy":
        # ПРОДВИНУТАЯ СИСТЕМА С ПРОКСИ
        if ADVANCED_SYSTEM_AVAILABLE:
            try:
                logging.info(f"🚀 [{topic_name}] Запрос через ПРОДВИНУТУЮ систему С ПРОКСИ")
                
                # Настраиваем продвинутую систему на работу с прокси
                advanced_system.proxy_mode = "enabled"
                if not advanced_system.current_proxy:
                    advanced_system._rotate_proxy()
                
                url = f"{Config.vinted_url}/api/v2/catalog/items"
                data = advanced_system.make_http_request(url, params, cookies)
                
                if data and "items" in data:
                    logging.info(f"✅ ПРОДВИНУТАЯ С ПРОКСИ: Found {len(data.get('items', []))} items for {topic_name}")
                    update_system_stats("advanced_proxy", success=True)
                else:
                    logging.warning(f"⚠️ Продвинутая система с прокси не вернула данные для {topic_name}")
                    update_system_stats("advanced_proxy", success=False)
                    
            except Exception as e:
                logging.error(f"❌ Ошибка продвинутой системы с прокси: {e}")
                update_system_stats("advanced_proxy", success=False)
        
        # Fallback на продвинутую без прокси (временный, не меняем current_system)
        if not data:
            logging.info(f"🛡️ [{topic_name}] ВРЕМЕННЫЙ fallback на ПРОДВИНУТУЮ БЕЗ ПРОКСИ")
            
            if ADVANCED_SYSTEM_AVAILABLE:
                try:
                    # Настраиваем продвинутую систему на работу без прокси
                    advanced_system.proxy_mode = "disabled"
                    advanced_system.current_proxy = None
                    
                    url = f"{Config.vinted_url}/api/v2/catalog/items"
                    data = advanced_system.make_http_request(url, params, cookies)
                    
                    if data and "items" in data:
                        logging.info(f"✅ ВРЕМЕННЫЙ FALLBACK: Found {len(data.get('items', []))} items через продвинутую без прокси")
                    else:
                        logging.warning(f"⚠️ Временный fallback не вернул данные для {topic_name}")
                        
                except Exception as e:
                    logging.error(f"❌ Ошибка временного fallback: {e}")
    
    # Обработка полученных данных
    if data and "items" in data:
        logging.info(f"📊 ИСПОЛЬЗУЕТСЯ СИСТЕМА: {used_system.upper()}")
        logging.info(f"Система [{used_system}]: Found {len(data['items'])} items")
        
        for item in data["items"]:
            if not bot_running:
                break
                
            # ИСПРАВЛЕННАЯ проверка исключений
            if should_exclude_item(item, exclude_catalog_ids):
                continue
                
            item_id = str(item["id"])
            item_url = item["url"]
            
            # Проверяем уникальность по ID и URL
            if item_id not in list_analyzed_items:
                item_title = item["title"]
                item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                item_image = item["photo"]["full_size_url"]
                item_size = item.get("size_title")

                priority_log = "🔥 PRIORITY " if is_priority else ""
                logging.info(f"🆕 {priority_log}NEW: {item_title} - {item_price} (ID: {item_id})")

                # НЕМЕДЛЕННО сохраняем item_id, чтобы избежать дублирования
                list_analyzed_items.append(item_id)
                save_analyzed_item(item_id)
                logging.info(f"💾 Saved item_id: {item_id}")

                # Send notifications
                if Config.smtp_username and Config.smtp_server:
                    send_email(item_title, item_price, item_url, item_image, item_size)

                if Config.slack_webhook_url:
                    send_slack_message(item_title, item_price, item_url, item_image, item_size)

                if Config.telegram_bot_token and Config.telegram_chat_id:
                    # АНТИБАН TELEGRAM ВКЛЮЧЕН В ФУНКЦИИ
                    success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
                    
                    if not success:
                        logging.warning(f"⚠️ Failed to send to Telegram: {item_title}")
            else:
                logging.info(f"🔄 SKIP: Already processed - {item.get('title', 'Unknown')} (ID: {item_id})")
    else:
        logging.warning(f"No items: {topic_name}")

# Telegram bot commands
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running, scan_mode, last_errors, telegram_errors, vinted_errors
    status = "🟢 Running" if bot_running else "🔴 Stopped"
    items_count = len(list_analyzed_items)
    
    mode_emoji = "🐰" if scan_mode == "fast" else "🐌"
    if scan_mode == "fast":
        mode_interval = "5-7s priority, 10-15s normal"
    else:
        mode_interval = "15-20s priority, 30-45s normal"
    mode_info = f"\n{mode_emoji} Mode: {scan_mode} ({mode_interval})"
    
    anti_info = f"\n📱 Telegram messages: {telegram_antiblock.message_count}"
    
    # ТРЕХУРОВНЕВАЯ СИСТЕМА СТАТУСА
    system_display = current_system.upper()
    if current_system == "advanced_no_proxy":
        system_display = "ADVANCED_NO_PROXY (без прокси)"
    elif current_system == "advanced_proxy":
        system_display = "ADVANCED_PROXY (с прокси)"
    elif current_system == "basic":
        system_display = "BASIC (базовая)"
    
    anti_info += f"\n🔄 ТЕКУЩАЯ СИСТЕМА: {system_display}"
    
    # Время работы в текущей системе
    time_in_current_system = time.time() - last_switch_time
    anti_info += f"\n⏱️ Время в системе: {time_in_current_system/60:.1f} мин"
    
    # Информация о переключениях
    if current_system == "advanced_proxy" and time_in_current_system > 120:
        anti_info += f"\n⚠️ Принудительное переключение через: {max(0, 120 - time_in_current_system):.0f}с"
    elif current_system == "basic" and time_in_current_system > 240:
        anti_info += f"\n⚠️ Принудительное переключение через: {max(0, 240 - time_in_current_system):.0f}с"
    
    # Статистика всех трех систем
    anti_info += f"\n📊 СТАТИСТИКА СИСТЕМ:"
    anti_info += f"\n🔹 Базовая система: {basic_success}/{basic_requests}"
    anti_info += f"\n🔹 Продвинутая без прокси: {advanced_no_proxy_success}/{advanced_no_proxy_requests}"
    anti_info += f"\n🔹 Продвинутая с прокси: {advanced_proxy_success}/{advanced_proxy_requests}"
    
    # Информация о продвинутой системе
    if ADVANCED_SYSTEM_AVAILABLE:
        anti_info += f"\n🚀 Продвинутая система:"
        anti_info += f"\n   📊 HTTP (без прокси): {advanced_no_proxy_success}/{advanced_no_proxy_requests}"
        anti_info += f"\n   📊 HTTP (с прокси): {advanced_proxy_success}/{advanced_proxy_requests}"
        
        # Информация о прокси
        if hasattr(advanced_system, 'proxies'):
            active_proxies = len([p for p in advanced_system.proxies if p not in advanced_system.proxy_blacklist])
            anti_info += f"\n   📡 Прокси: {active_proxies} активных"
        
        # Информация об ошибках
        total_advanced_errors = advanced_no_proxy_errors + advanced_proxy_errors
        anti_info += f"\n   ⚠️ Ошибок подряд: {total_advanced_errors}/{max_errors_before_switch * 2}"
        anti_info += f"\n   🔄 Режим: {system_mode}"
    else:
        anti_info += f"\n❌ Продвинутая система недоступна"
    
    # Общая успешность
    total_requests = basic_requests + advanced_no_proxy_requests + advanced_proxy_requests
    total_success = basic_success + advanced_no_proxy_success + advanced_proxy_success
    overall_success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
    
    anti_info += f"\n📈 Общая успешность: {overall_success_rate:.1f}%"
    
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
            
        last_lines = lines[-20:] if len(lines) >= 20 else lines
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
    """Команда /fast - быстрый режим сканирования"""
    global scan_mode
    scan_mode = "fast"
    logging.info("🐰 Переключение в FAST режим")
    await update.message.reply_text("🐰 FAST mode: 5-7s priority, 10-15s normal")

async def slow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /slow - медленный режим сканирования"""
    global scan_mode
    scan_mode = "slow"
    logging.info("🐌 Переключение в SLOW режим")
    await update.message.reply_text("🐌 SLOW mode: 25-35s priority, 45-60s normal")



async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сброс системы и статистики"""
    try:
        global advanced_system_errors, basic_system_errors
        
        # Сброс счетчиков ошибок
        advanced_system_errors = 0
        basic_system_errors = 0
        
        # Сброс продвинутой системы
        if ADVANCED_SYSTEM_AVAILABLE:
            try:
                advanced_system.refresh_session()
                advanced_system.consecutive_errors = 0
                advanced_system.current_delay = 1.0
                # Сброс к режиму auto без прокси
                advanced_system.reset_to_auto_mode()
                logging.info("🔄 Продвинутая система сброшена к режиму auto")
            except Exception as e:
                logging.error(f"❌ Ошибка сброса продвинутой системы: {e}")
        
        # Очистка ошибок
        global last_errors, telegram_errors, vinted_errors
        last_errors.clear()
        telegram_errors.clear()
        vinted_errors.clear()
        
        message = "🔄 Система сброшена:\n"
        message += "✅ Счетчики ошибок очищены\n"
        message += "✅ Продвинутая система перезапущена\n"
        message += "✅ Режим сброшен к auto (экономия трафика)\n"
        message += "✅ История ошибок очищена\n"
        message += "🔄 Готов к работе!"
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )
        
    except Exception as e:
        logging.error(f"❌ Ошибка команды reset: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Ошибка сброса: {str(e)[:50]}"
        )

async def proxy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /proxy - статус продвинутой системы"""
    if ADVANCED_SYSTEM_AVAILABLE:
        try:
            stats = advanced_system.get_stats()
            
            # Статистика трехуровневой системы
            message = "🚀 СТАТУС ПРОДВИНУТОЙ СИСТЕМЫ:\n\n"
            message += f"🔄 ТЕКУЩАЯ СИСТЕМА: {current_system.upper()}\n"
            message += f"📊 СТАТИСТИКА СИСТЕМ:\n"
            message += f"🔹 Базовая система: {basic_success}/{basic_requests}\n"
            message += f"🔹 Продвинутая без прокси: {advanced_no_proxy_success}/{advanced_no_proxy_requests}\n"
            message += f"🔹 Продвинутая с прокси: {advanced_proxy_success}/{advanced_proxy_requests}\n\n"
            
            # Статистика продвинутой системы
            message += f"📊 HTTP запросы: {stats['http_success']}/{stats['http_requests']}\n"
            message += f"📈 Общая успешность: {stats['success_rate']:.1f}%\n"
            message += f"📡 Прокси: ✅ {stats['proxies_count']} активных\n"
            message += f"🔄 Текущий прокси: {stats['current_proxy']}\n"
            message += f"⚠️ Ошибки 403: {stats['errors_403']}\n"
            message += f"⚠️ Ошибки 429: {stats['errors_429']}\n" 
            message += f"⚠️ Ошибки 521: {stats['errors_521']}\n"
            message += f"🔄 Ошибок подряд: {stats['consecutive_errors']}\n"
            message += f"🎯 Режим системы: {system_mode}\n\n"
            
            # НОВАЯ ИНФОРМАЦИЯ О ПРОКСИ
            message += f"🧠 УМНАЯ САМОВОССТАНАВЛИВАЮЩАЯСЯ СИСТЕМА:\n"
            message += f"📊 Режим прокси: {stats['proxy_mode']}\n"
            message += f"✅ Успехов прокси: {stats['proxy_successes']}\n"
            message += f"❌ Ошибок прокси: {stats['proxy_failures']}\n"
            message += f"🔧 Использует прокси: {'Да' if stats['should_use_proxy'] else 'Нет'}\n\n"
            
            # НОВАЯ СТАТИСТИКА САМОВОССТАНОВЛЕНИЯ
            message += f"🔄 САМОВОССТАНОВЛЕНИЕ:\n"
            message += f"📋 Whitelist прокси: {stats['proxy_whitelist_count']}\n"
            message += f"🚫 Blacklist прокси: {stats['proxy_blacklist_count']}\n"
            message += f"🔄 Попыток восстановления: {stats['proxy_recovery_attempts']}/5\n"
            message += f"🔄 Переключений режимов: {stats['mode_switch_count']}\n"
            message += f"📊 Последнее переключение: {stats['last_mode_switch']}\n\n"
            
            # Статистика прокси с здоровьем
            if stats.get('proxy_stats'):
                message += "📊 СТАТИСТИКА ПРОКСИ (с здоровьем):\n"
                active_proxies = 0
                for proxy, proxy_stat in stats['proxy_stats'].items():
                    if proxy_stat['requests'] > 0:  # Показываем только активные прокси
                        active_proxies += 1
                        health_emoji = "🟢" if proxy_stat['health_score'] >= 80 else "🟡" if proxy_stat['health_score'] >= 50 else "🔴"
                        message += f"{health_emoji} {proxy}: {proxy_stat['success']}/{proxy_stat['requests']} ({proxy_stat['success_rate']:.1f}%) [Здоровье: {proxy_stat['health_score']}]\n"
                
                if active_proxies == 0:
                    message += "📊 Нет активных прокси\n"
            else:
                message += "📊 Статистика прокси недоступна\n"
                
        except Exception as e:
            message = f"❌ Ошибка получения статистики: {str(e)[:100]}"
    else:
        message = "🚀 СТАТУС ПРОДВИНУТОЙ СИСТЕМЫ:\n\n❌ Система недоступна\n🔄 Используется базовая система"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /system - переключение между системами"""
    global system_mode
    
    if context.args:
        new_mode = context.args[0].lower()
        if new_mode in ["auto", "basic", "advanced", "proxy", "noproxy"]:
            system_mode = new_mode
            
            # Управление прокси в продвинутой системе
            if ADVANCED_SYSTEM_AVAILABLE:
                if new_mode == "proxy":
                    advanced_system.enable_proxies()
                    message = f"🔄 Режим системы изменен на: {system_mode} (с прокси)"
                elif new_mode == "noproxy":
                    advanced_system.disable_proxies()
                    message = f"🔄 Режим системы изменен на: {system_mode} (без прокси)"
                else:
                    message = f"🔄 Режим системы изменен на: {system_mode}"
            else:
                message = f"🔄 Режим системы изменен на: {system_mode}"
        else:
            message = "❌ Доступные режимы: auto, basic, advanced, proxy, noproxy"
    else:
        message = f"🎯 Текущий режим: {system_mode}\n\n"
        message += "📖 Доступные режимы:\n"
        message += "• auto - автоматическое переключение\n"
        message += "• basic - только базовая система\n" 
        message += "• advanced - только продвинутая система\n"
        message += "• proxy - продвинутая с прокси\n"
        message += "• noproxy - продвинутая без прокси\n\n"
        message += "Использование: /system proxy"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def redeploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /redeploy - перезапуск Railway при банах"""
    global advanced_system_errors, basic_system_errors
    
    message = "🔄 АВТОМАТИЧЕСКИЙ REDEPLOY:\n\n"
    
    # Проверяем критичность ситуации
    total_errors = advanced_system_errors + basic_system_errors
    if total_errors >= max_system_errors * 1.5:
        message += "⚠️ КРИТИЧЕСКИЙ УРОВЕНЬ БЛОКИРОВОК!\n"
        message += f"📊 Ошибок продвинутой: {advanced_system_errors}\n"
        message += f"📊 Ошибок базовой: {basic_system_errors}\n\n"
        
        # Имитация redeploy через Railway API (в реальности нужен Railway token)
        message += "🚀 Попытка автоматического redeploy...\n"
        
        # Сброс счетчиков ошибок для симуляции restart
        advanced_system_errors = 0
        basic_system_errors = 0
        
        message += "✅ Счетчики ошибок сброшены\n"
        message += "💡 Для полного redeploy настройте Railway Webhook"
    else:
        message += f"📊 Ошибок продвинутой: {advanced_system_errors}/{max_system_errors}\n"
        message += f"📊 Ошибок базовой: {basic_system_errors}/{max_system_errors}\n"
        message += "✅ Уровень ошибок в норме, redeploy не требуется"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def recovery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /recovery - управление самовосстанавливающейся системой"""
    if not ADVANCED_SYSTEM_AVAILABLE:
        message = "❌ Продвинутая система недоступна\n🔄 Используется базовая система"
        await telegram_antiblock.safe_send_message(update.effective_chat.id, message)
        return
        
    if context.args:
        action = context.args[0].lower()
        
        if action == "test":
            # Принудительное тестирование прокси
            message = "🔍 ПРИНУДИТЕЛЬНОЕ ТЕСТИРОВАНИЕ ПРОКСИ:\n\n"
            
            try:
                # Тестируем все прокси
                working_proxies = []
                failed_proxies = []
                
                for proxy in advanced_system.proxies:
                    if advanced_system._test_proxy(proxy):
                        working_proxies.append(f"{proxy['host']}:{proxy['port']}")
                        if proxy not in advanced_system.proxy_whitelist:
                            advanced_system.proxy_whitelist.append(proxy)
                    else:
                        failed_proxies.append(f"{proxy['host']}:{proxy['port']}")
                        if proxy not in advanced_system.proxy_blacklist:
                            advanced_system.proxy_blacklist.append(proxy)
                
                message += f"✅ Рабочих прокси: {len(working_proxies)}\n"
                message += f"❌ Неисправных прокси: {len(failed_proxies)}\n\n"
                
                if working_proxies:
                    message += "✅ РАБОЧИЕ ПРОКСИ:\n"
                    for proxy in working_proxies[:5]:  # Показываем первые 5
                        message += f"• {proxy}\n"
                        
                if failed_proxies:
                    message += "\n❌ НЕИСПРАВНЫЕ ПРОКСИ:\n"
                    for proxy in failed_proxies[:5]:  # Показываем первые 5
                        message += f"• {proxy}\n"
                        
            except Exception as e:
                message += f"❌ Ошибка тестирования: {str(e)[:100]}"
                    
        elif action == "reset":
            # Сброс всех списков
            try:
                advanced_system.proxy_whitelist.clear()
                advanced_system.proxy_blacklist.clear()
                advanced_system.proxy_recovery_attempts = 0
                advanced_system.mode_switch_count = 0
                
                # Сброс здоровья всех прокси
                for proxy in advanced_system.proxies:
                    proxy['health_score'] = 100
                    proxy['errors'] = 0
                    proxy['success'] = 0
                    
                message = "🔄 СБРОС САМОВОССТАНАВЛИВАЮЩЕЙСЯ СИСТЕМЫ:\n\n"
                message += "✅ Whitelist очищен\n"
                message += "✅ Blacklist очищен\n"
                message += "✅ Счетчики восстановления сброшены\n"
                message += "✅ Здоровье прокси восстановлено\n"
                
            except Exception as e:
                message = f"❌ Ошибка сброса: {str(e)[:100]}"
            
        elif action == "force_proxy":
            # Принудительное включение прокси
            try:
                advanced_system.proxy_mode = "enabled"
                advanced_system._rotate_proxy()
                message = "🔧 ПРИНУДИТЕЛЬНОЕ ВКЛЮЧЕНИЕ ПРОКСИ:\n\n"
                message += "✅ Режим прокси включен\n"
                if advanced_system.current_proxy:
                    message += f"🔄 Текущий прокси: {advanced_system.current_proxy['host']}:{advanced_system.current_proxy['port']}\n"
                else:
                    message += "⚠️ Нет доступных прокси\n"
                    
            except Exception as e:
                message = f"❌ Ошибка включения прокси: {str(e)[:100]}"
                
        elif action == "force_noproxy":
            # Принудительное отключение прокси
            try:
                advanced_system.proxy_mode = "disabled"
                advanced_system.current_proxy = None
                message = "🚫 ПРИНУДИТЕЛЬНОЕ ОТКЛЮЧЕНИЕ ПРОКСИ:\n\n"
                message += "✅ Режим прокси отключен\n"
                
            except Exception as e:
                message = f"❌ Ошибка отключения прокси: {str(e)[:100]}"
                
        elif action == "force_advanced":
            # Принудительное переключение на продвинутую систему
            try:
                global current_system
                current_system = "advanced_no_proxy"
                message = "🚀 ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ НА ПРОДВИНУТУЮ СИСТЕМУ:\n\n"
                message += "✅ Система переключена на advanced_no_proxy\n"
                message += "✅ Прокси отключены\n"
                message += "🔄 Готов к работе с продвинутой системой\n"
                
            except Exception as e:
                message = f"❌ Ошибка переключения: {str(e)[:100]}"
            
        else:
            message = "❌ Неизвестное действие. Доступные действия:\n"
            message += "• /recovery test - тестирование прокси\n"
            message += "• /recovery reset - сброс системы\n"
            message += "• /recovery force_proxy - принудительное включение прокси\n"
            message += "• /recovery force_noproxy - принудительное отключение прокси\n"
            message += "• /recovery force_advanced - принудительное переключение на продвинутую систему\n"
    else:
        # Показываем статус самовосстановления
        try:
            stats = advanced_system.get_stats()
            message = "🔄 СТАТУС САМОВОССТАНАВЛИВАЮЩЕЙСЯ СИСТЕМЫ:\n\n"
            message += f"📊 Режим: {stats['proxy_mode']}\n"
            message += f"📋 Whitelist: {stats['proxy_whitelist_count']} прокси\n"
            message += f"🚫 Blacklist: {stats['proxy_blacklist_count']} прокси\n"
            message += f"🔄 Попыток восстановления: {stats['proxy_recovery_attempts']}/5\n"
            message += f"🔄 Переключений режимов: {stats['mode_switch_count']}\n"
            message += f"📊 Последнее переключение: {stats['last_mode_switch']}\n\n"
            
            message += "📖 Доступные команды:\n"
            message += "• /recovery test - тестирование прокси\n"
            message += "• /recovery reset - сброс системы\n"
            message += "• /recovery force_proxy - принудительное включение прокси\n"
            message += "• /recovery force_noproxy - принудительное отключение прокси\n"
            
        except Exception as e:
            message = f"❌ Ошибка получения статуса: {str(e)[:100]}"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def traffic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /traffic - мониторинг экономии трафика прокси"""
    if ADVANCED_SYSTEM_AVAILABLE:
        try:
            stats = advanced_system.get_stats()
            
            # Расчет экономии трафика на основе трехуровневой системы
            total_requests = basic_requests + advanced_no_proxy_requests + advanced_proxy_requests
            proxy_requests = advanced_proxy_requests
            no_proxy_requests = basic_requests + advanced_no_proxy_requests
            traffic_savings = (no_proxy_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Расчет стоимости
            proxy_cost_per_request = 0.001  # Примерная стоимость прокси запроса
            saved_cost = no_proxy_requests * proxy_cost_per_request
            
            message = "💰 МОНИТОРИНГ ЭКОНОМИИ ТРАФИКА:\n\n"
            message += f"📊 Общих запросов: {total_requests}\n"
            message += f"📡 Запросов через прокси: {proxy_requests}\n"
            message += f"🚫 Запросов без прокси: {no_proxy_requests}\n"
            message += f"💾 Экономия трафика: {traffic_savings:.1f}%\n"
            message += f"💰 Сэкономлено средств: ${saved_cost:.2f}\n\n"
            
            # Статистика по режимам
            message += "🎯 РЕЖИМЫ РАБОТЫ:\n"
            message += f"🔄 Текущая система: {current_system.upper()}\n"
            message += f"📊 Режим системы: {system_mode}\n"
            
            # Общая успешность трехуровневой системы
            total_success = basic_success + advanced_no_proxy_success + advanced_proxy_success
            overall_success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
            message += f"📈 Успешность: {overall_success_rate:.1f}%\n"
            
            # Ошибки трехуровневой системы
            total_errors = basic_system_errors + advanced_no_proxy_errors + advanced_proxy_errors
            message += f"⚠️ Ошибок подряд: {total_errors}\n\n"
            
            # Рекомендации
            message += "💡 РЕКОМЕНДАЦИИ:\n"
            if current_system == "basic" and basic_system_errors >= 2:
                message += "🔧 Рекомендуется: переключение на продвинутую систему\n"
            elif current_system == "advanced_proxy" and traffic_savings < 50:
                message += "🔧 Рекомендуется: /recovery force_noproxy\n"
            elif overall_success_rate < 70:
                message += "🔄 Рекомендуется: /recovery force_proxy\n"
            else:
                message += "✅ Система работает оптимально\n"
                
            # Прогноз экономии
            daily_requests = 21000  # Примерно в режиме /fast
            daily_savings = (daily_requests * traffic_savings / 100) * proxy_cost_per_request
            monthly_savings = daily_savings * 30
            
            message += f"\n📈 ПРОГНОЗ ЭКОНОМИИ:\n"
            message += f"💰 В день: ${daily_savings:.2f}\n"
            message += f"💰 В месяц: ${monthly_savings:.2f}\n"
            
        except Exception as e:
            message = f"❌ Ошибка получения статистики трафика: {str(e)[:100]}"
    else:
        # Статистика только базовой системы
        total_requests = basic_requests
        total_success = basic_success
        overall_success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        
        message = "💰 МОНИТОРИНГ ЭКОНОМИИ ТРАФИКА:\n\n"
        message += f"📊 Общих запросов: {total_requests}\n"
        message += f"📡 Запросов через прокси: 0\n"
        message += f"🚫 Запросов без прокси: {total_requests}\n"
        message += f"💾 Экономия трафика: 100.0%\n"
        message += f"💰 Сэкономлено средств: ${total_requests * 0.001:.2f}\n\n"
        
        message += "🎯 РЕЖИМЫ РАБОТЫ:\n"
        message += f"🔄 Текущая система: {current_system.upper()}\n"
        message += f"📊 Режим системы: {system_mode}\n"
        message += f"📈 Успешность: {overall_success_rate:.1f}%\n"
        message += f"⚠️ Ошибок подряд: {basic_system_errors}\n\n"
        
        message += "💡 РЕКОМЕНДАЦИИ:\n"
        if basic_system_errors >= 2:
            message += "🔧 Рекомендуется: продвинутая система недоступна\n"
        else:
            message += "✅ Базовая система работает стабильно\n"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /topics - проверка доступности топиков"""
    message = "🏷️ ПРОВЕРКА ДОСТУПНОСТИ ТОПИКОВ:\n\n"
    
    # Проверяем каждый топик
    for topic_name, topic_data in Config.topics.items():
        thread_id = topic_data.get('thread_id')
        if thread_id:
            try:
                # Пробуем отправить тестовое сообщение в топик
                test_params = {
                    "chat_id": Config.telegram_chat_id,
                    "text": f"🔍 Тест топика: {topic_name}",
                    "message_thread_id": thread_id
                }
                
                response = requests.post(
                    f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                    data=test_params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    message += f"✅ {topic_name} (ID: {thread_id})\n"
                elif response.status_code == 400:
                    message += f"❌ {topic_name} (ID: {thread_id}) - недоступен\n"
                else:
                    message += f"⚠️ {topic_name} (ID: {thread_id}) - ошибка {response.status_code}\n"
                    
            except Exception as e:
                message += f"❌ {topic_name} (ID: {thread_id}) - ошибка: {str(e)[:30]}\n"
        else:
            message += f"⚠️ {topic_name} - нет thread_id\n"
    
    message += f"\n💡 РЕКОМЕНДАЦИИ:\n"
    message += f"• Если топики недоступны, вещи будут отправляться в основной чат\n"
    message += f"• Добавьте участников в чат (нужно 200+) для активации топиков\n"
    message += f"• Или используйте отдельные чаты для каждой категории\n"
    
    await telegram_antiblock.safe_send_message(update.effective_chat.id, message)

async def threadid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения thread_id топика из Telegram"""
    try:
        # Получаем thread_id из сообщения
        if update.message and update.message.reply_to_message:
            # Если это ответ на сообщение в топике
            thread_id = update.message.reply_to_message.message_thread_id
            if thread_id:
                await telegram_antiblock.safe_send_message(update.effective_chat.id, f"📌 Thread ID: {thread_id}")
            else:
                await telegram_antiblock.safe_send_message(update.effective_chat.id, "📌 Thread ID: НЕТ (основной чат)")
        else:
            # Если команда отправлена в топике, получаем thread_id текущего топика
            thread_id = update.message.message_thread_id if update.message else None
            if thread_id:
                await telegram_antiblock.safe_send_message(update.effective_chat.id, f"📌 Thread ID: {thread_id}")
            else:
                await telegram_antiblock.safe_send_message(update.effective_chat.id, "📌 Thread ID: НЕТ (основной чат)")
    except Exception as e:
        await telegram_antiblock.safe_send_message(update.effective_chat.id, f"❌ Ошибка: {str(e)}")

async def detect_threadid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для автоматического определения thread_id топика"""
    try:
        message = "🔍 АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ THREAD_ID:\n\n"
        
        # Получаем thread_id текущего топика
        current_thread_id = update.message.message_thread_id if update.message else None
        
        if current_thread_id:
            message += f"📌 Текущий топик: {current_thread_id}\n"
            message += f"✅ Команда отправлена в топик\n"
            
            # Проверяем, есть ли этот thread_id в конфигурации
            found_topics = []
            for topic_name, topic_data in Config.topics.items():
                if topic_data.get("thread_id") == current_thread_id:
                    found_topics.append(topic_name)
            
            if found_topics:
                message += f"📋 Найденные топики в конфигурации:\n"
                for topic in found_topics:
                    message += f"  • {topic}\n"
            else:
                message += f"⚠️ Этот thread_id НЕ найден в конфигурации\n"
                message += f"💡 Добавьте его в Config.py для автоматической отправки\n"
        else:
            message += f"📌 Основной чат (без thread_id)\n"
            message += f"⚠️ Сообщения будут отправляться в основной чат\n"
        
        message += f"\n💡 ИНФОРМАЦИЯ:\n"
        message += f"• Thread ID определяет, куда отправляются товары\n"
        message += f"• Если ID в конфигурации → товары в топик\n"
        message += f"• Если ID НЕ в конфигурации → товары в основной чат\n"
        
        await telegram_antiblock.safe_send_message(update.effective_chat.id, message)
        
    except Exception as e:
        await telegram_antiblock.safe_send_message(update.effective_chat.id, f"❌ Ошибка: {str(e)}")

async def setup_bot():
    application = Application.builder().token(Config.telegram_bot_token).build()
    
    # Основные команды (10)
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("log", log_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("fast", fast_command))
    application.add_handler(CommandHandler("slow", slow_command))
    application.add_handler(CommandHandler("recovery", recovery_command))
    application.add_handler(CommandHandler("traffic", traffic_command))
    application.add_handler(CommandHandler("system", system_command))
    application.add_handler(CommandHandler("redeploy", redeploy_command))
    application.add_handler(CommandHandler("topics", topics_command))
    
    # Дополнительные команды (3)
    application.add_handler(CommandHandler("proxy", proxy_command))
    application.add_handler(CommandHandler("threadid", threadid_command))
    application.add_handler(CommandHandler("detect", detect_threadid_command))
    
    return application

def auto_recovery_system():
    """Автоматическая система самовосстановления"""
    global current_system, basic_system_errors, advanced_no_proxy_errors, advanced_proxy_errors, last_switch_time
    global recovery_threshold, stuck_time_threshold
    
    if ADVANCED_SYSTEM_AVAILABLE:
        if advanced_system.consecutive_errors > 30:
            logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Сброс ошибок (было: {advanced_system.consecutive_errors})")
            advanced_system.consecutive_errors = 0
            advanced_system.errors_403 = 0
            advanced_system.errors_429 = 0
            advanced_system.errors_521 = 0
        
        if len(advanced_system.proxy_blacklist) > len(advanced_system.proxy_whitelist) * 2:
            logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Очистка blacklist прокси")
            advanced_system.proxy_blacklist.clear()
        
        if current_system == "advanced_proxy" and advanced_proxy_errors > 8:
            logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Переключение с прокси на без прокси")
            current_system = "advanced_no_proxy"
            advanced_proxy_errors = 0
            advanced_system.proxy_mode = "disabled"
            advanced_system.current_proxy = None
        
        if current_system == "basic" and time.time() - last_switch_time > 480:
            logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Переключение с basic на продвинутую")
            current_system = "advanced_no_proxy"
            last_switch_time = time.time()
    
    if telegram_antiblock.consecutive_errors > 8:
        logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ TG: Сброс ошибок (было: {telegram_antiblock.consecutive_errors})")
        telegram_antiblock.consecutive_errors = 0
        telegram_antiblock.error_backoff = 1
    
    total_errors = basic_system_errors + advanced_no_proxy_errors + advanced_proxy_errors
    if total_errors > recovery_threshold:
        logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Критический уровень ошибок ({total_errors})")
        
        basic_system_errors = 0
        advanced_no_proxy_errors = 0
        advanced_proxy_errors = 0
        
        if ADVANCED_SYSTEM_AVAILABLE:
            current_system = "advanced_no_proxy"
            logging.info(f"🔄 САМОВОССТАНОВЛЕНИЕ: Переключение на advanced_no_proxy")
        else:
            current_system = "basic"
            logging.info(f"🔄 САМОВОССТАНОВЛЕНИЕ: Переключение на basic")
        
        last_switch_time = time.time()
    
    time_in_current_system = time.time() - last_switch_time
    if time_in_current_system > stuck_time_threshold:
        logging.warning(f"🔄 АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ: Застревание в системе {current_system} ({time_in_current_system/60:.1f} минут)")
        
        if current_system == "basic" and ADVANCED_SYSTEM_AVAILABLE:
            current_system = "advanced_no_proxy"
            logging.info(f"🔄 САМОВОССТАНОВЛЕНИЕ: Принудительное переключение на advanced_no_proxy")
        elif current_system == "advanced_no_proxy":
            current_system = "advanced_proxy"
            logging.info(f"🔄 САМОВОССТАНОВЛЕНИЕ: Принудительное переключение на advanced_proxy")
        elif current_system == "advanced_proxy":
            current_system = "advanced_no_proxy"
            logging.info(f"🔄 САМОВОССТАНОВЛЕНИЕ: Принудительное переключение обратно на advanced_no_proxy")
        
        last_switch_time = time.time()

def signal_handler(signum, frame):
    global bot_running
    logging.info("🛑 Получен сигнал завершения, останавливаю систему...")
    bot_running = False

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
