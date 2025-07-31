#!/usr/bin/env python3
"""
Продвинутая система антибана с браузерной эмуляцией и прокси
Для стабильной версии v1.0
"""

import asyncio
import time
import random
import logging
import requests
import json
from typing import Dict, List, Optional
from fake_useragent import UserAgent
import Config

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("⚠️ Playwright недоступен, используется только HTTP режим")

class AdvancedAntiBan:
    """Продвинутая двухуровневая система антибана"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Состояние браузерной системы
        self.playwright = None
        self.browser = None
        self.context = None  
        self.page = None
        self.browser_available = False
        
        # Настройки системы
        self.max_retries = 3
        self.backoff_factor = 2.0
        self.current_delay = 1.0
        self.max_delay = 30.0
        
        # Статистика
        self.http_requests = 0
        self.http_success = 0
        self.browser_requests = 0
        self.browser_success = 0
        self.errors_403 = 0
        self.errors_429 = 0
        self.errors_521 = 0
        self.consecutive_errors = 0
        
        # Прокси из конфигурации
        self.proxy_pool = []
        self.current_proxy_index = 0
        self.load_proxies()
        
        # Сессии и куки
        self.session_cookies = {}
        self.session_created = time.time()
        self.session_requests = 0
        self.max_session_requests = 50
        
    def load_proxies(self):
        """Загрузка прокси из конфигурации"""
        # Прокси отключены - работаем без них
        logging.info("📡 Продвинутая система работает БЕЗ прокси")
        
    def get_current_proxy(self):
        """Получение текущего прокси"""
        return None  # Без прокси
        
    def rotate_proxy(self):
        """Ротация прокси"""
        # Без прокси - ничего не делаем
        pass
    
    def get_random_headers(self):
        """Генерация случайных заголовков как у настоящего браузера"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8,ru;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    def human_delay(self):
        """Имитация человеческих задержек (0.5-3с)"""
        delay = random.uniform(0.5, 3.0)
        time.sleep(delay)
    
    def exponential_backoff(self):
        """Экспоненциальный backoff при ошибках"""
        delay = min(self.current_delay * self.backoff_factor, self.max_delay)
        self.current_delay = delay
        logging.warning(f"⏳ Backoff delay: {delay:.1f}s")
        time.sleep(delay)
    
    def reset_backoff(self):
        """Сброс backoff при успешном запросе"""
        self.current_delay = 1.0
        self.consecutive_errors = 0
    
    async def initialize_browser(self):
        """Инициализация браузерной системы"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
            
        try:
            self.playwright = await async_playwright().start()
            
            # Настройки для обхода детекции
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--user-agent=' + self.ua.random
            ]
            
            # Запуск браузера БЕЗ прокси
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=browser_args
            )
            
            # Создание контекста с антидетекцией
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.ua.random,
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers=self.get_random_headers()
            )
            
            # Добавляем скрипты для обхода детекции
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)
            
            self.browser_available = True
            logging.info("✅ Браузерная система инициализирована")
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка инициализации браузера: {e}")
            self.browser_available = False
            return False
    
    def make_http_request(self, url: str, params: dict) -> Optional[dict]:
        """HTTP запрос с антибаном"""
        self.http_requests += 1
        self.session_requests += 1
        
        # Автоматическая инициализация браузера при первом запросе
        if not self.browser_available and PLAYWRIGHT_AVAILABLE:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(self.initialize_browser())
                loop.close()
                if success:
                    logging.info("✅ Браузер автоматически инициализирован")
                else:
                    logging.warning("⚠️ Автоматическая инициализация браузера не удалась")
            except Exception as e:
                logging.error(f"❌ Ошибка автоматической инициализации: {e}")
        
        try:
            # Проверка необходимости обновления сессии
            if (self.session_requests > self.max_session_requests or 
                time.time() - self.session_created > 1800):  # 30 минут
                self.refresh_session()
            
            # Запрос БЕЗ прокси с улучшенными заголовками
            headers = self.get_random_headers()
            logging.info(f"🌐 Продвинутая система: HTTP запрос к {url}")
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
                cookies=self.session_cookies
            )
            
            logging.info(f"📊 HTTP статус: {response.status_code}")
            if response.status_code != 200:
                logging.warning(f"⚠️ HTTP ошибка: {response.status_code} - {response.text[:100]}")
            
            # Обработка ответа
            if response.status_code == 200:
                self.http_success += 1
                self.reset_backoff()
                
                # Сохранение куки
                self.session_cookies.update(response.cookies)
                
                return response.json()
                
            elif response.status_code == 403:
                self.errors_403 += 1
                self.consecutive_errors += 1
                logging.warning(f"🚫 HTTP 403 Forbidden (ошибок подряд: {self.consecutive_errors})")
                
            elif response.status_code == 429:
                self.errors_429 += 1
                self.consecutive_errors += 1
                logging.warning(f"⏱️ HTTP 429 Too Many Requests")
                
            elif response.status_code == 521:
                self.errors_521 += 1
                self.consecutive_errors += 1
                logging.warning(f"🔧 HTTP 521 Server Down")
                
            # При множественных ошибках - ротация прокси
            if self.consecutive_errors >= 3:
                self.rotate_proxy()
                self.refresh_session()
                
            return None
            
        except Exception as e:
            logging.error(f"❌ HTTP ошибка: {e}")
            self.consecutive_errors += 1
            return None
    
    async def make_browser_request(self, url: str, params: dict) -> Optional[dict]:
        """Браузерный запрос с обработкой JS"""
        if not self.browser_available:
            return None
            
        self.browser_requests += 1
        
        try:
            # Формирование URL с параметрами
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_str}"
            
            # Навигация с обработкой Cloudflare
            await self.page.goto(full_url, wait_until='networkidle')
            
            # Ждем возможных редиректов Cloudflare
            await asyncio.sleep(random.uniform(2, 5))
            
            # Попытка найти JSON данные
            try:
                # Метод 1: Прямое чтение ответа как JSON
                content = await self.page.content()
                if content.strip().startswith('{'):
                    data = json.loads(content)
                    self.browser_success += 1
                    self.reset_backoff()
                    return data
                
                # Метод 2: Поиск JSON в элементах страницы  
                json_element = await self.page.query_selector('pre')
                if json_element:
                    json_text = await json_element.text_content()
                    if json_text.strip().startswith('{'):
                        data = json.loads(json_text)
                        self.browser_success += 1
                        self.reset_backoff()
                        return data
                        
            except json.JSONDecodeError:
                pass
            
            # Проверка на блокировку Cloudflare
            title = await self.page.title()
            if 'cloudflare' in title.lower() or 'checking' in title.lower():
                logging.warning("🌩️ Обнаружена страница Cloudflare")
                await asyncio.sleep(10)  # Ждем прохождения проверки
                return None
                
            logging.warning("⚠️ Браузер: не найден JSON ответ")
            return None
            
        except Exception as e:
            logging.error(f"❌ Браузерная ошибка: {e}")
            return None
    
    def refresh_session(self):
        """Обновление HTTP сессии"""
        self.session.close()
        self.session = requests.Session()
        self.session_cookies = {}
        self.session_created = time.time()
        self.session_requests = 0
        logging.info("🔄 HTTP сессия обновлена")
    
    async def close(self):
        """Закрытие ресурсов"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.session.close()
            logging.info("✅ Продвинутая система закрыта")
        except Exception as e:
            logging.error(f"❌ Ошибка закрытия: {e}")
    
    def get_stats(self):
        """Получение статистики"""
        total_requests = self.http_requests + self.browser_requests
        total_success = self.http_success + self.browser_success
        
        return {
            'http_requests': self.http_requests,
            'http_success': self.http_success,
            'browser_requests': self.browser_requests,
            'browser_success': self.browser_success,
            'total_requests': total_requests,
            'total_success': total_success,
            'success_rate': (total_success / max(total_requests, 1)) * 100,
            'errors_403': self.errors_403,
            'errors_429': self.errors_429,
            'errors_521': self.errors_521,
            'consecutive_errors': self.consecutive_errors,
            'browser_available': self.browser_available,
            'proxies_count': 0,  # Без прокси
            'current_proxy': None  # Без прокси
        }

# Глобальный экземпляр
advanced_system = AdvancedAntiBan()