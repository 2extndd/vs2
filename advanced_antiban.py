#!/usr/bin/env python3
"""
Продвинутая система антибана с резидентскими прокси и кластеризацией
Для стабильной версии v1.1 (Railway compatible)
УМНАЯ САМОВОССТАНАВЛИВАЮЩАЯСЯ СИСТЕМА
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
        self.browser_requests = 0
        self.browser_success = 0
        self.errors_403 = 0
        self.errors_429 = 0
        self.errors_521 = 0
        self.consecutive_errors = 0
        
        # Система прокси
        self.proxies = []
        self.current_proxy = None
        self.proxy_rotation_count = 0
        self.max_requests_per_proxy = 5  # Ротация каждые 5 запросов
        
        # УМНАЯ САМОВОССТАНАВЛИВАЮЩАЯСЯ СИСТЕМА ПРОКСИ
        self.proxy_mode = "auto"  # auto, enabled, disabled
        self.proxy_health_check_time = time.time()
        self.proxy_health_check_interval = 180  # 3 минуты (уменьшено для быстрой реакции)
        self.proxy_failure_threshold = 8  # Количество ошибок для отключения прокси (уменьшено)
        self.proxy_success_threshold = 3   # Количество успехов для включения прокси (уменьшено)
        self.proxy_failures = 0
        self.proxy_successes = 0
        
        # НОВАЯ СИСТЕМА АВТОМАТИЧЕСКОГО ВОССТАНОВЛЕНИЯ
        self.last_proxy_test_time = time.time()
        self.proxy_test_interval = 600  # 10 минут - тестируем прокси каждые 10 минут
        self.proxy_recovery_attempts = 0
        self.max_proxy_recovery_attempts = 5
        self.proxy_blacklist = []  # Список заблокированных прокси
        self.proxy_whitelist = []  # Список проверенных рабочих прокси
        
        # Система автоматического переключения режимов
        self.mode_switch_time = time.time()
        self.mode_switch_interval = 300  # 5 минут между переключениями
        self.last_mode_switch = "auto"
        self.mode_switch_count = 0
        self.max_mode_switches = 10  # Максимум переключений в час
        
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
        
        # Первоначальная проверка здоровья прокси
        self._check_proxy_health()
        
        # Запуск фоновой задачи для периодической проверки прокси
        self._start_background_tasks()
        
    def _start_background_tasks(self):
        """Запуск фоновых задач для самовосстановления"""
        try:
            # Создаем фоновую задачу для периодической проверки прокси
            import threading
            self.background_thread = threading.Thread(target=self._background_proxy_checker, daemon=True)
            self.background_thread.start()
            logging.info("🔄 Фоновая задача проверки прокси запущена")
        except Exception as e:
            logging.error(f"❌ Ошибка запуска фоновой задачи: {e}")
        
    def _background_proxy_checker(self):
        """Фоновая задача для периодической проверки и восстановления прокси"""
        while True:
            try:
                time.sleep(60)  # Проверяем каждую минуту
                self._periodic_proxy_health_check()
                self._attempt_proxy_recovery()
                self._cleanup_proxy_lists()
            except Exception as e:
                logging.error(f"❌ Ошибка в фоновой задаче: {e}")
                
    def _periodic_proxy_health_check(self):
        """Периодическая проверка здоровья прокси"""
        current_time = time.time()
        
        # Проверяем каждые 3 минуты
        if current_time - self.proxy_health_check_time > self.proxy_health_check_interval:
            self.proxy_health_check_time = current_time
            
            # Анализируем статистику
            total_errors = self.errors_403 + self.errors_429 + self.errors_521
            success_rate = (self.http_success / self.http_requests * 100) if self.http_requests > 0 else 0
            
            logging.info(f"🔍 Периодическая проверка прокси:")
            logging.info(f"📊 Успешность: {success_rate:.1f}%")
            logging.info(f"📊 Ошибок: {total_errors}")
            logging.info(f"📊 Режим: {self.proxy_mode}")
            
            # Автоматическое переключение режимов
            if self.proxy_mode == "auto":
                if total_errors >= self.proxy_failure_threshold and success_rate < 50:
                    self._switch_to_no_proxy_mode()
                elif self.proxy_successes >= self.proxy_success_threshold and success_rate > 70:
                    self._switch_to_proxy_mode()
                    
    def _switch_to_no_proxy_mode(self):
        """Переключение в режим без прокси"""
        if self.proxy_mode != "disabled":
            self.proxy_mode = "disabled"
            self.current_proxy = None
            self.proxy_failures = 0
            self.proxy_successes = 0
            self.mode_switch_count += 1
            logging.warning("🚫 АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ: Режим без прокси")
            
    def _switch_to_proxy_mode(self):
        """Переключение в режим с прокси"""
        if self.proxy_mode != "enabled" and self.proxies:
            self.proxy_mode = "enabled"
            self._rotate_proxy()
            self.proxy_failures = 0
            self.proxy_successes = 0
            self.mode_switch_count += 1
            logging.info("✅ АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ: Режим с прокси")
            
    def _attempt_proxy_recovery(self):
        """Попытка восстановления прокси"""
        current_time = time.time()
        
        # Пытаемся восстановить прокси каждые 10 минут
        if current_time - self.last_proxy_test_time > self.proxy_test_interval:
            self.last_proxy_test_time = current_time
            
            if self.proxy_mode == "disabled" and self.proxy_recovery_attempts < self.max_proxy_recovery_attempts:
                logging.info("🔄 Попытка восстановления прокси...")
                
                # Тестируем случайные прокси
                test_proxies = [p for p in self.proxies if p not in self.proxy_blacklist]
                if test_proxies:
                    test_proxy = random.choice(test_proxies)
                    if self._test_proxy(test_proxy):
                        self.proxy_whitelist.append(test_proxy)
                        self.proxy_recovery_attempts = 0
                        logging.info("✅ Прокси восстановлен и добавлен в whitelist")
                        
                        # Переключаемся обратно в режим прокси
                        if len(self.proxy_whitelist) >= 2:
                            self._switch_to_proxy_mode()
                    else:
                        self.proxy_blacklist.append(test_proxy)
                        self.proxy_recovery_attempts += 1
                        logging.warning(f"❌ Прокси не работает, попытка {self.proxy_recovery_attempts}/{self.max_proxy_recovery_attempts}")
                        
    def _test_proxy(self, proxy):
        """Тестирование прокси"""
        try:
            test_url = "https://httpbin.org/ip"
            proxy_dict = {
                'http': proxy['http'],
                'https': proxy['https']
            }
            
            response = requests.get(test_url, proxies=proxy_dict, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
        
    def _cleanup_proxy_lists(self):
        """Очистка списков прокси"""
        current_time = time.time()
        
        # Очищаем blacklist каждые 30 минут
        if len(self.proxy_blacklist) > 0 and current_time - self.proxy_health_check_time > 1800:
            self.proxy_blacklist.clear()
            logging.info("🧹 Blacklist прокси очищен")
            
        # Ограничиваем размер whitelist
        if len(self.proxy_whitelist) > 10:
            self.proxy_whitelist = self.proxy_whitelist[-10:]
            
    def _load_proxies(self):
        """Загрузка резидентских прокси"""
        proxy_list = [
            "uxhsjsf86p:QjN9YOVXOTh404nh@93.190.142.89:22423",
            "uxhsjsf86p:QjN9YOVXOTh404nh@212.41.8.52:11291", 
            "uxhsjsf86p:QjN9YOVXOTh404nh@62.112.10.76:13303",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.165.241.5:11902",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.100.232.163:23018",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.185.51.65:13546",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.185.51.65:19564",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.100.232.132:11391",
            "uxhsjsf86p:QjN9YOVXOTh404nh@89.39.104.152:20487",
            "uxhsjsf86p:QjN9YOVXOTh404nh@175.110.113.246:20028",
            "uxhsjsf86p:QjN9YOVXOTh404nh@175.110.113.245:15595",
            "uxhsjsf86p:QjN9YOVXOTh404nh@175.110.113.236:22517",
            "uxhsjsf86p:QjN9YOVXOTh404nh@93.190.139.73:16653",
            "uxhsjsf86p:QjN9YOVXOTh404nh@185.165.240.228:17405",
            "uxhsjsf86p:QjN9YOVXOTh404nh@175.110.115.54:15846",
            "uxhsjsf86p:QjN9YOVXOTh404nh@151.106.6.79:17750",
            "uxhsjsf86p:QjN9YOVXOTh404nh@190.2.132.231:13961",
            "uxhsjsf86p:QjN9YOVXOTh404nh@93.190.139.245:19441",
            "uxhsjsf86p:QjN9YOVXOTh404nh@93.190.141.73:25919",
            "uxhsjsf86p:QjN9YOVXOTh404nh@136.243.177.154:23567"
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
                    'errors': 0,
                    'last_used': 0,
                    'health_score': 100  # Новый параметр здоровья прокси
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
        """Умная ротация прокси с учетом здоровья"""
        if not self.proxies:
            return None
            
        # Сначала пробуем прокси из whitelist
        if self.proxy_whitelist:
            self.current_proxy = random.choice(self.proxy_whitelist)
        else:
            # Выбираем прокси с лучшим здоровьем
            available_proxies = [p for p in self.proxies if p not in self.proxy_blacklist and p['health_score'] > 50]
            if not available_proxies:
                available_proxies = [p for p in self.proxies if p not in self.proxy_blacklist]
            if not available_proxies:
                available_proxies = self.proxies
                
            # Сортируем по здоровью
            available_proxies.sort(key=lambda x: x['health_score'], reverse=True)
            self.current_proxy = available_proxies[0] if available_proxies else None
            
        if self.current_proxy:
            self.proxy_rotation_count = 0
            self.current_proxy['last_used'] = time.time()
            logging.info(f"🔄 Ротация прокси: {self.current_proxy['host']}:{self.current_proxy['port']} (здоровье: {self.current_proxy['health_score']})")
            
        return self.current_proxy
        
    def disable_proxies(self):
        """Отключение прокси"""
        self.current_proxy = None
        self.proxy_mode = "disabled"
        logging.info("📡 Прокси отключены")
        
    def enable_proxies(self):
        """Включение прокси"""
        if self.proxies:
            self.proxy_mode = "enabled"
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
        """HTTP запрос с антибаном и умной системой прокси"""
        logging.info(f"🚀 Продвинутая система (ID: {id(self)}): Начинаем HTTP запрос")
        self.http_requests += 1
        self.session_requests += 1
        
        # Проверка здоровья прокси
        self._check_proxy_health()
        
        # Проверка необходимости ротации прокси (только если используем прокси)
        if self._should_use_proxy() and self.proxies and (self.proxy_rotation_count >= self.max_requests_per_proxy or 
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
            
            # УМНАЯ САМОВОССТАНАВЛИВАЮЩАЯСЯ СИСТЕМА ПРОКСИ
            if self._should_use_proxy() and self.current_proxy:
                logging.info(f"🔧 Прокси: {self.current_proxy['host']}:{self.current_proxy['port']} (режим: {self.proxy_mode})")
                proxy_dict = {
                    'http': self.current_proxy['http'],
                    'https': self.current_proxy['https']
                }
                # Обновляем статистику прокси
                self.current_proxy['requests'] += 1
                self.proxy_rotation_count += 1
            else:
                logging.info(f"🔧 Прокси: ❌ Отключен (режим: {self.proxy_mode})")
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
                    self._update_proxy_health(self.current_proxy, False)
                
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
                    self.proxy_successes += 1
                    self._update_proxy_health(self.current_proxy, True)
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
                    self.proxy_failures += 1
                    self._update_proxy_health(self.current_proxy, False)
                logging.warning(f"🚫 HTTP 403 Forbidden (ошибок подряд: {self.consecutive_errors})")
                
            elif response.status_code == 429:
                self.errors_429 += 1
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                    self.proxy_failures += 1
                    self._update_proxy_health(self.current_proxy, False)
                logging.warning(f"⏱️ HTTP 429 Too Many Requests")
                
            elif response.status_code == 521:
                self.errors_521 += 1
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                    self.proxy_failures += 1
                    self._update_proxy_health(self.current_proxy, False)
                logging.warning(f"🔧 HTTP 521 Server Down")
                
            else:
                # Обработка других ошибок (401, 500, etc.)
                self.consecutive_errors += 1
                if self.current_proxy:
                    self.current_proxy['errors'] += 1
                    self.proxy_failures += 1
                    self._update_proxy_health(self.current_proxy, False)
                logging.warning(f"⚠️ HTTP {response.status_code}: {response.text[:100]}")
                
            # При множественных ошибках - ротация прокси или отключение
            if self.consecutive_errors >= 3:
                if self._should_use_proxy() and self.proxies:
                    self._rotate_proxy()
                self.refresh_session()
                
            return None
            
        except Exception as e:
            logging.error(f"❌ HTTP ошибка: {e}")
            self.consecutive_errors += 1
            if self.current_proxy:
                self.current_proxy['errors'] += 1
                self.proxy_failures += 1
                self._update_proxy_health(self.current_proxy, False)
            return None
    
    def _update_proxy_health(self, proxy, success: bool):
        """Обновление здоровья прокси"""
        if success:
            # Увеличиваем здоровье при успехе
            proxy['health_score'] = min(100, proxy['health_score'] + 10)
            if proxy['health_score'] >= 80 and proxy not in self.proxy_whitelist:
                self.proxy_whitelist.append(proxy)
                logging.info(f"✅ Прокси {proxy['host']}:{proxy['port']} добавлен в whitelist")
        else:
            # Уменьшаем здоровье при ошибке
            proxy['health_score'] = max(0, proxy['health_score'] - 20)
            if proxy['health_score'] <= 20 and proxy in self.proxy_whitelist:
                self.proxy_whitelist.remove(proxy)
                logging.warning(f"❌ Прокси {proxy['host']}:{proxy['port']} удален из whitelist")
            elif proxy['health_score'] <= 0:
                self.proxy_blacklist.append(proxy)
                logging.error(f"🚫 Прокси {proxy['host']}:{proxy['port']} добавлен в blacklist")

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
        """Получение статистики системы"""
        total_requests = self.http_requests + self.browser_requests
        total_success = self.http_success + self.browser_success
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0.0
        
        # Статистика прокси
        proxy_stats = {}
        for proxy in self.proxies:
            proxy_key = f"{proxy['host']}:{proxy['port']}"
            requests = proxy.get('requests', 0)
            success = proxy.get('success', 0)
            errors = proxy.get('errors', 0)
            proxy_success_rate = (success / requests * 100) if requests > 0 else 0.0
            
            proxy_stats[proxy_key] = {
                'requests': requests,
                'success': success,
                'errors': errors,
                'success_rate': proxy_success_rate,
                'health_score': proxy.get('health_score', 100)
            }
        
        stats = {
            'http_requests': self.http_requests,
            'http_success': self.http_success,
            'browser_requests': self.browser_requests,
            'browser_success': self.browser_success,
            'total_requests': total_requests,
            'total_success': total_success,
            'success_rate': success_rate,
            'errors_403': self.errors_403,
            'errors_429': self.errors_429,
            'errors_521': self.errors_521,
            'consecutive_errors': self.consecutive_errors,
            'browser_available': PLAYWRIGHT_AVAILABLE,
            'proxies_count': len(self.proxies),
            'current_proxy': f"{self.current_proxy['host']}:{self.current_proxy['port']}" if self.current_proxy else "None",
            'proxy_stats': proxy_stats,
            # НОВАЯ СТАТИСТИКА ПРОКСИ
            'proxy_mode': self.proxy_mode,
            'proxy_failures': self.proxy_failures,
            'proxy_successes': self.proxy_successes,
            'proxy_health_check_time': self.proxy_health_check_time,
            'should_use_proxy': self._should_use_proxy(),
            # НОВАЯ СТАТИСТИКА САМОВОССТАНОВЛЕНИЯ
            'proxy_whitelist_count': len(self.proxy_whitelist),
            'proxy_blacklist_count': len(self.proxy_blacklist),
            'proxy_recovery_attempts': self.proxy_recovery_attempts,
            'mode_switch_count': self.mode_switch_count,
            'last_mode_switch': self.last_mode_switch
        }
        
        return stats

    def _check_proxy_health(self):
        """Проверка здоровья прокси и автоматическое переключение режимов"""
        current_time = time.time()
        
        # Проверяем, нужно ли обновить статус прокси
        if current_time - self.proxy_health_check_time > self.proxy_health_check_interval:
            self.proxy_health_check_time = current_time
            
            # Анализируем статистику ошибок
            total_errors = self.errors_403 + self.errors_429 + self.errors_521
            
            if self.proxy_mode == "auto":
                if total_errors >= self.proxy_failure_threshold and self.proxy_failures >= 3:
                    # Отключаем прокси при множественных ошибках
                    self._disable_proxy_mode()
                    logging.warning(f"🚫 Прокси отключены из-за {total_errors} ошибок")
                elif self.proxy_successes >= self.proxy_success_threshold and self.proxy_failures < 2:
                    # Включаем прокси при успехах
                    self._enable_proxy_mode()
                    logging.info(f"✅ Прокси включены после {self.proxy_successes} успехов")
    
    def _enable_proxy_mode(self):
        """Включение режима прокси"""
        if self.proxies and not self.current_proxy:
            self.proxy_mode = "enabled"
            self._rotate_proxy()
            self.proxy_failures = 0
            self.proxy_successes = 0
            logging.info("🔄 Режим прокси включен")
    
    def _disable_proxy_mode(self):
        """Отключение режима прокси"""
        self.proxy_mode = "disabled"
        self.current_proxy = None
        self.proxy_failures = 0
        self.proxy_successes = 0
        logging.info("🚫 Режим прокси отключен")
    
    def _should_use_proxy(self):
        """Определяет, нужно ли использовать прокси"""
        if self.proxy_mode == "disabled":
            return False
        elif self.proxy_mode == "enabled":
            return True
        else:  # auto mode
            # Используем прокси, если нет критических ошибок
            total_errors = self.errors_403 + self.errors_429 + self.errors_521
            return total_errors < self.proxy_failure_threshold

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