#!/usr/bin/env python3
"""
Продвинутая система антибана только с HTTP запросами
Для стабильной версии v1.1 (Railway compatible)
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

# Используется только HTTP режим для Railway совместимости
PLAYWRIGHT_AVAILABLE = False

class AdvancedAntiBan:
    """Продвинутая двухуровневая система антибана"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Настройки системы
        self.max_retries = 3
        self.backoff_factor = 2.0
        self.current_delay = 1.0
        self.max_delay = 30.0
        
        # Статистика
        self.http_requests = 0
        self.http_success = 0
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
    

    def make_http_request(self, url: str, params: dict, cookies: dict = None) -> Optional[dict]:
        """HTTP запрос с антибаном"""
        logging.info(f"🚀 Продвинутая система (ID: {id(self)}): Начинаем HTTP запрос")
        self.http_requests += 1
        self.session_requests += 1
        

        # Используем переданные cookies или получаем новые
        if cookies is None:
            try:
                import Config
                main_url = Config.vinted_url
                headers = self.get_random_headers()
                
                # Получаем cookies через POST запрос
                self.session.post(main_url, headers=headers, timeout=30)
                cookies = self.session.cookies.get_dict()
                logging.info(f"🍪 Получены новые cookies: {cookies}")
                
            except Exception as e:
                logging.warning(f"⚠️ Ошибка получения cookies: {e}")
                cookies = {}
        else:
            logging.info(f"🍪 Используем переданные cookies: {cookies}")
        
        try:
            # Проверка необходимости обновления сессии
            if (self.session_requests > self.max_session_requests or 
                time.time() - self.session_created > 1800):  # 30 минут
                self.refresh_session()
            
            # Запрос БЕЗ прокси с улучшенными заголовками и cookies
            headers = self.get_random_headers()
            logging.info(f"🌐 Продвинутая система: HTTP запрос к {url}")
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
                cookies=cookies  # Используем свежие cookies
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
                
                logging.info(f"✅ Продвинутая система (ID: {id(self)}): HTTP успех! Счетчики: {self.http_requests}/{self.http_success}")
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
                
            else:
                # Обработка других ошибок (401, 500, etc.)
                self.consecutive_errors += 1
                logging.warning(f"⚠️ HTTP {response.status_code}: {response.text[:100]}")
                
            # При множественных ошибках - ротация прокси
            if self.consecutive_errors >= 3:
                self.rotate_proxy()
                self.refresh_session()
                
            return None
            
        except Exception as e:
            logging.error(f"❌ HTTP ошибка: {e}")
            self.consecutive_errors += 1
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
            self.session.close()
            logging.info("✅ Продвинутая система закрыта")
        except Exception as e:
            logging.error(f"❌ Ошибка закрытия: {e}")
    
    def get_stats(self):
        """Получение статистики"""
        total_requests = self.http_requests
        total_success = self.http_success
        
        stats = {
            'http_requests': self.http_requests,
            'http_success': self.http_success,
            'browser_requests': 0,
            'browser_success': 0,
            'total_requests': total_requests,
            'total_success': total_success,
            'success_rate': (total_success / max(total_requests, 1)) * 100,
            'errors_403': self.errors_403,
            'errors_429': self.errors_429,
            'errors_521': self.errors_521,
            'consecutive_errors': self.consecutive_errors,
            'browser_available': False,
            'proxies_count': 0,  # Без прокси
            'current_proxy': None  # Без прокси
        }
        
        logging.info(f"📊 Статистика продвинутой системы (ID: {id(self)}): HTTP={self.http_requests}/{self.http_success}")
        return stats

# Глобальный экземпляр (синглтон)
_advanced_system_instance = None

def get_advanced_system():
    """Получение глобального экземпляра продвинутой системы"""
    global _advanced_system_instance
    if _advanced_system_instance is None:
        _advanced_system_instance = AdvancedAntiBan()
        logging.info(f"🚀 Продвинутая система инициализирована: {id(_advanced_system_instance)}")
    return _advanced_system_instance

# Для обратной совместимости
advanced_system = get_advanced_system()