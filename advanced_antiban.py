#!/usr/bin/env python3
"""
Продвинутая система антибана с резидентскими прокси и кластеризацией
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
    """Продвинутая система антибана с прокси и кластеризацией"""
    
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
        
        # Система прокси
        self.proxies = []
        self.current_proxy = None
        self.proxy_rotation_count = 0
        self.max_requests_per_proxy = 5  # Ротация каждые 5 запросов
        
        # Кластеризация антибот-параметров
        self.client_profiles = self._generate_client_profiles()
        self.current_profile = None
        
        # Сессионные данные
        self.session_cookies = {}
        self.session_created = time.time()
        self.session_requests = 0
        self.max_session_requests = 50
        
        # Статистика прокси
        self.proxy_stats = {}
        
        # Инициализация прокси
        self._load_proxies()
        
    def _load_proxies(self):
        """Загрузка резидентских прокси"""
        proxy_list = [
            "uxhsjsf86p:QjN9YOVXOTh404nh@175.110.113.245:23250",
            "uxhsjsf86p:QjN9YOVXOTh404nh@93.190.137.111:13196", 
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.100.232.163:26649",
            "uxhsjsf86p:QjN9YOVXOTh404nh@91.232.105.44:11829"
        ]
        
        for proxy in proxy_list:
            try:
                username, password = proxy.split('@')[0].split(':')
                host, port = proxy.split('@')[1].split(':')
                
                proxy_dict = {
                    'http': f'http://{username}:{password}@{host}:{port}',
                    'https': f'http://{username}:{password}@{host}:{port}',
                    'host': host,
                    'port': port,
                    'requests': 0,
                    'success': 0,
                    'errors': 0
                }
                self.proxies.append(proxy_dict)
                logging.info(f"✅ Загружен прокси: {host}:{port}")
                
            except Exception as e:
                logging.error(f"❌ Ошибка загрузки прокси {proxy}: {e}")
        
        logging.info(f"📊 Загружено прокси: {len(self.proxies)}")
        
    def _generate_client_profiles(self):
        """Генерация профилей клиентов для кластеризации"""
        profiles = []
        
        # Chrome на разных ОС
        chrome_profiles = [
            {
                'name': 'Chrome-Windows',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept': 'application/json, text/plain, */*',
                'accept_language': 'en-US,en;q=0.9,de;q=0.8',
                'accept_encoding': 'gzip, deflate, br',
                'sec_fetch_dest': 'empty',
                'sec_fetch_mode': 'cors',
                'sec_fetch_site': 'same-origin'
            },
            {
                'name': 'Chrome-MacOS',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept': 'application/json, text/plain, */*',
                'accept_language': 'en-US,en;q=0.9,de;q=0.8',
                'accept_encoding': 'gzip, deflate, br',
                'sec_fetch_dest': 'empty',
                'sec_fetch_mode': 'cors',
                'sec_fetch_site': 'same-origin'
            }
        ]
        
        # Firefox профили
        firefox_profiles = [
            {
                'name': 'Firefox-Windows',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'accept': 'application/json, text/plain, */*',
                'accept_language': 'en-US,en;q=0.9,de;q=0.8',
                'accept_encoding': 'gzip, deflate, br',
                'sec_fetch_dest': 'empty',
                'sec_fetch_mode': 'cors',
                'sec_fetch_site': 'same-origin'
            },
            {
                'name': 'Firefox-MacOS',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
                'accept': 'application/json, text/plain, */*',
                'accept_language': 'en-US,en;q=0.9,de;q=0.8',
                'accept_encoding': 'gzip, deflate, br',
                'sec_fetch_dest': 'empty',
                'sec_fetch_mode': 'cors',
                'sec_fetch_site': 'same-origin'
            }
        ]
        
        profiles.extend(chrome_profiles)
        profiles.extend(firefox_profiles)
        
        logging.info(f"🎭 Создано профилей клиентов: {len(profiles)}")
        return profiles
        
    def _get_random_profile(self):
        """Получение случайного профиля клиента"""
        return random.choice(self.client_profiles)
        
    def _rotate_proxy(self):
        """Ротация прокси"""
        if not self.proxies:
            return None
            
        # Выбираем прокси с наименьшим количеством ошибок
        available_proxies = [p for p in self.proxies if p['errors'] < 3]
        if not available_proxies:
            available_proxies = self.proxies
            
        # Выбираем случайный прокси
        self.current_proxy = random.choice(available_proxies)
        self.proxy_rotation_count = 0
        
        logging.info(f"🔄 Ротация прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
        return self.current_proxy
        
    def disable_proxies(self):
        """Отключение прокси"""
        self.current_proxy = None
        logging.info("📡 Прокси отключены")
        
    def enable_proxies(self):
        """Включение прокси"""
        if self.proxies:
            self._rotate_proxy()
            logging.info("📡 Прокси включены")
        else:
            logging.warning("⚠️ Нет доступных прокси")
        
    def get_random_headers(self):
        """Генерация заголовков с кластеризацией"""
        profile = self._get_random_profile()
        self.current_profile = profile
        
        headers = {
            "User-Agent": profile['user_agent'],
            "Accept": profile['accept'],
            "Accept-Language": profile['accept_language'],
            "Accept-Encoding": profile['accept_encoding'],
            "DNT": "1",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Sec-Fetch-Dest": profile['sec_fetch_dest'],
            "Sec-Fetch-Mode": profile['sec_fetch_mode'],
            "Sec-Fetch-Site": profile['sec_fetch_site']
        }
        
        return headers
    
    def human_delay(self):
        """Человекоподобные задержки"""
        # Увеличиваем задержки при ошибках
        if self.consecutive_errors > 0:
            base_delay = 2.0 + (self.consecutive_errors * 1.5)
            delay = random.uniform(base_delay, base_delay + 3.0)
        else:
            delay = random.uniform(1.0, 3.0)
        
        logging.info(f"⏱️ Задержка: {delay:.1f}s")
        time.sleep(delay)

    def exponential_backoff(self):
        """Экспоненциальная задержка при ошибках"""
        if self.consecutive_errors > 0:
            self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
            delay = random.uniform(self.current_delay * 0.8, self.current_delay * 1.2)
            logging.warning(f"🚫 Экспоненциальная задержка: {delay:.1f}s (ошибок: {self.consecutive_errors})")
            time.sleep(delay)
        else:
            self.human_delay()

    def reset_backoff(self):
        """Сброс задержек при успехе"""
        if self.consecutive_errors > 0:
            logging.info(f"✅ Сброс задержек (было ошибок: {self.consecutive_errors})")
        self.consecutive_errors = 0
        self.current_delay = 1.0
    

    def make_http_request(self, url: str, params: dict, cookies: dict = None) -> Optional[dict]:
        """HTTP запрос с антибаном и прокси"""
        logging.info(f"🚀 Продвинутая система (ID: {id(self)}): Начинаем HTTP запрос")
        self.http_requests += 1
        self.session_requests += 1
        
        # Проверка необходимости ротации прокси (только если есть прокси)
        if self.proxies and (self.proxy_rotation_count >= self.max_requests_per_proxy or 
            self.current_proxy is None):
            self._rotate_proxy()
        
        # УЛУЧШЕННАЯ СИСТЕМА ПОЛУЧЕНИЯ COOKIES
        if cookies is None or not cookies:
            try:
                import Config
                main_url = Config.vinted_url
                headers = self.get_random_headers()
                
                # Сначала получаем основную страницу для cookies
                logging.info(f"🍪 Получаем новые cookies с {main_url}")
                main_response = self.session.get(main_url, headers=headers, timeout=30)
                
                if main_response.status_code == 200:
                    cookies = self.session.cookies.get_dict()
                    logging.info(f"✅ Получены cookies: {cookies}")
                else:
                    logging.warning(f"⚠️ Ошибка получения cookies: HTTP {main_response.status_code}")
                    cookies = {}
                    
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
            
            # Запрос с прокси и улучшенными заголовками
            headers = self.get_random_headers()
            logging.info(f"🌐 Продвинутая система: HTTP запрос к {url}")
            logging.info(f"🔧 Профиль: {self.current_profile['name']}")
            
            # Подготовка запроса с или без прокси
            if self.current_proxy:
                logging.info(f"🔧 Прокси: {self.current_proxy['host']}:{self.current_proxy['port']}")
                proxy_dict = {
                    'http': self.current_proxy['http'],
                    'https': self.current_proxy['https']
                }
                # Обновляем статистику прокси
                self.current_proxy['requests'] += 1
                self.proxy_rotation_count += 1
            else:
                logging.info(f"🔧 Прокси: ❌ Отключен")
                proxy_dict = None
                self.proxy_rotation_count += 1
            
            logging.info(f"🔧 Параметры: {params}")
            logging.info(f"🍪 Cookies: {cookies}")
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                proxies=proxy_dict,
                timeout=30,
                cookies=cookies
            )
            
            logging.info(f"📝 Ответ: {response.text[:200]}")
            logging.info(f"📊 HTTP статус: {response.status_code}")
            
            # ОБРАБОТКА ОШИБКИ 401 - ПЕРЕАУТЕНТИФИКАЦИЯ
            if response.status_code == 401:
                logging.warning(f"🚫 HTTP 401 - Недействительный токен аутентификации")
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                
                # Попытка переаутентификации
                try:
                    logging.info(f"🔄 Попытка переаутентификации...")
                    import Config
                    main_url = Config.vinted_url
                    
                    # Очищаем старые cookies
                    self.session.cookies.clear()
                    
                    # Получаем новые cookies
                    main_response = self.session.get(main_url, headers=headers, timeout=30)
                    if main_response.status_code == 200:
                        new_cookies = self.session.cookies.get_dict()
                        logging.info(f"✅ Новые cookies получены: {new_cookies}")
                        
                        # Повторяем запрос с новыми cookies
                        response = self.session.get(
                            url,
                            params=params,
                            headers=headers,
                            proxies=proxy_dict,
                            timeout=30,
                            cookies=new_cookies
                        )
                        logging.info(f"🔄 Повторный запрос: HTTP {response.status_code}")
                    else:
                        logging.error(f"❌ Не удалось получить новые cookies: HTTP {main_response.status_code}")
                        
                except Exception as e:
                    logging.error(f"❌ Ошибка переаутентификации: {e}")
            
            if response.status_code != 200:
                logging.warning(f"⚠️ HTTP ошибка: {response.status_code} - {response.text[:100]}")
            
            # Обработка ответа
            if response.status_code == 200:
                self.http_success += 1
                if self.current_proxy:
                    self.current_proxy['success'] += 1
                self.reset_backoff()
                
                # Сохранение куки
                self.session_cookies.update(response.cookies)
                
                logging.info(f"✅ Продвинутая система (ID: {id(self)}): HTTP успех! Счетчики: {self.http_requests}/{self.http_success}")
                return response.json()
                
            elif response.status_code == 403:
                self.errors_403 += 1
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                logging.warning(f"🚫 HTTP 403 Forbidden (ошибок подряд: {self.consecutive_errors})")
                
            elif response.status_code == 429:
                self.errors_429 += 1
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                logging.warning(f"⏱️ HTTP 429 Too Many Requests")
                
            elif response.status_code == 521:
                self.errors_521 += 1
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                logging.warning(f"🔧 HTTP 521 Server Down")
                
            else:
                # Обработка других ошибок (401, 500, etc.)
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                logging.warning(f"⚠️ HTTP {response.status_code}: {response.text[:100]}")
                
            # При множественных ошибках - ротация прокси
            if self.consecutive_errors >= 3 and self.proxies:
                self._rotate_proxy()
                self.refresh_session()
                
            return None
            
        except Exception as e:
            logging.error(f"❌ HTTP ошибка: {e}")
            self.consecutive_errors += 1
            if self.current_proxy:
                self.current_proxy['errors'] += 1
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
        """Получение статистики с информацией о прокси"""
        total_requests = self.http_requests
        total_success = self.http_success
        
        # Статистика прокси
        proxy_stats = {}
        for proxy in self.proxies:
            if proxy['requests'] > 0:
                success_rate = (proxy['success'] / proxy['requests']) * 100
                proxy_stats[f"{proxy['host']}:{proxy['port']}"] = {
                    'requests': proxy['requests'],
                    'success': proxy['success'],
                    'errors': proxy['errors'],
                    'success_rate': success_rate
                }
        
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
            'proxies_count': len(self.proxies),
            'current_proxy': f"{self.current_proxy['host']}:{self.current_proxy['port']}" if self.current_proxy else None,
            'proxy_stats': proxy_stats
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