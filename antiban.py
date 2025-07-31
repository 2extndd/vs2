#!/usr/bin/env python3
"""
Продвинутая антибан система для Vinted Scanner
Включает: прокси, браузер, ротацию IP, эмуляцию человека
"""

import asyncio
import random
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Browser, Page
import aiohttp
import aiofiles

@dataclass
class ProxyConfig:
    """Конфигурация прокси"""
    host: str
    port: int
    username: str
    password: str
    country: str = "DE"
    type: str = "residential"

@dataclass
class SessionData:
    """Данные сессии"""
    cookies: Dict
    headers: Dict
    user_agent: str
    proxy: Optional[ProxyConfig]
    created_at: datetime
    requests_count: int = 0
    errors_count: int = 0
    last_error: Optional[str] = None

class AdvancedAntiBan:
    """Продвинутая антибан система"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.sessions: List[SessionData] = []
        self.current_session_index = 0
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Прокси пул (замените на реальные)
        self.proxy_pool = [
            ProxyConfig("proxy1.example.com", 8080, "user1", "pass1"),
            ProxyConfig("proxy2.example.com", 8080, "user2", "pass2"),
            ProxyConfig("proxy3.example.com", 8080, "user3", "pass3"),
        ]
        
        # Статистика
        self.total_requests = 0
        self.total_errors = 0
        self.total_blocks = 0
        self.last_rotation = time.time()
        
        # Настройки
        self.max_requests_per_session = 10
        self.max_errors_per_session = 3
        self.rotation_interval = 300  # 5 минут
        self.backoff_multiplier = 2.0
        
        # Инициализация
        self._init_sessions()
    
    def _init_sessions(self):
        """Инициализация сессий"""
        for i, proxy in enumerate(self.proxy_pool):
            session = SessionData(
                cookies={},
                headers=self._generate_headers(),
                user_agent=self.ua.random,
                proxy=proxy,
                created_at=datetime.now()
            )
            self.sessions.append(session)
    
    def _generate_headers(self) -> Dict:
        """Генерация случайных заголовков браузера"""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    async def _init_browser(self):
        """Инициализация headless браузера"""
        if not self.browser:
            playwright = await async_playwright().start()
            proxy = self.sessions[self.current_session_index].proxy
            
            browser_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
            
            if proxy:
                browser_args.extend([
                    f"--proxy-server={proxy.host}:{proxy.port}",
                    f"--proxy-auth={proxy.username}:{proxy.password}"
                ])
            
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=browser_args
            )
            
            self.page = await self.browser.new_page()
            await self.page.set_extra_http_headers(self.sessions[self.current_session_index].headers)
            # Устанавливаем User-Agent через контекст
            await self.page.context.set_extra_http_headers({
                'User-Agent': self.sessions[self.current_session_index].user_agent
            })
    
    async def _rotate_session(self):
        """Ротация сессии"""
        old_index = self.current_session_index
        self.current_session_index = (self.current_session_index + 1) % len(self.sessions)
        
        logging.info(f"🔄 Ротация сессии: {old_index} -> {self.current_session_index}")
        
        # Пересоздаем браузер с новым прокси
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
        
        await self._init_browser()
    
    async def _handle_error(self, error: str, status_code: int = None):
        """Обработка ошибок с автоматической ротацией"""
        current_session = self.sessions[self.current_session_index]
        current_session.errors_count += 1
        current_session.last_error = error
        
        self.total_errors += 1
        
        if status_code in [403, 429, 503, 521]:
            self.total_blocks += 1
            logging.warning(f"🚫 Блокировка: {status_code} - {error}")
        
        # Ротация при превышении лимитов
        if (current_session.errors_count >= self.max_errors_per_session or 
            current_session.requests_count >= self.max_requests_per_session or
            time.time() - self.last_rotation > self.rotation_interval):
            
            await self._rotate_session()
            self.last_rotation = time.time()
        
        # Экспоненциальный backoff
        backoff_time = min(300, (2 ** current_session.errors_count) * self.backoff_multiplier)
        logging.info(f"⏳ Backoff: {backoff_time:.1f}s")
        await asyncio.sleep(backoff_time)
    
    async def smart_request(self, url: str, params: Dict = None) -> Tuple[Optional[Dict], bool]:
        """Умный запрос с антибан защитой"""
        try:
            await self._init_browser()
            
            # Добавляем случайную задержку
            delay = random.uniform(0.5, 3.0)
            await asyncio.sleep(delay)
            
            # Формируем URL с параметрами
            full_url = url
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                full_url = f"{url}?{query_string}"
            
            # Выполняем запрос через браузер
            response = await self.page.goto(full_url, wait_until="networkidle")
            
            if response.status == 200:
                # Получаем контент
                content = await self.page.content()
                
                # Парсим JSON из контента
                try:
                    # Ищем JSON в скриптах
                    json_data = await self.page.evaluate("""
                        () => {
                            const scripts = document.querySelectorAll('script');
                            for (const script of scripts) {
                                if (script.textContent.includes('window.__INITIAL_STATE__')) {
                                    const match = script.textContent.match(/window\\.__INITIAL_STATE__\\s*=\\s*({.*?});/);
                                    if (match) {
                                        return JSON.parse(match[1]);
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                    
                    if json_data:
                        self.sessions[self.current_session_index].requests_count += 1
                        self.total_requests += 1
                        return json_data, True
                    else:
                        # Fallback: парсим как обычный HTML
                        return {"html": content}, True
                        
                except Exception as e:
                    logging.error(f"❌ Ошибка парсинга JSON: {str(e)[:50]}")
                    return None, False
                    
            else:
                await self._handle_error(f"HTTP {response.status}", response.status)
                return None, False
                
        except Exception as e:
            await self._handle_error(str(e))
            return None, False
    
    async def get_vinted_items(self, search_params: Dict) -> Optional[Dict]:
        """Получение товаров с Vinted через антибан систему"""
        url = "https://www.vinted.de/api/v2/catalog/items"
        
        # Добавляем случайные параметры для маскировки
        params = search_params.copy()
        params["_t"] = int(time.time() * 1000)  # Timestamp
        params["_r"] = random.randint(1000, 9999)  # Random
        
        result, success = await self.smart_request(url, params)
        
        if success and result:
            logging.info(f"✅ Успешный запрос: {len(result.get('items', []))} товаров")
            return result
        else:
            logging.error(f"❌ Неудачный запрос к Vinted")
            return None
    
    def get_stats(self) -> Dict:
        """Получение статистики антибан системы"""
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_blocks": self.total_blocks,
            "current_session": self.current_session_index,
            "sessions_count": len(self.sessions),
            "success_rate": (self.total_requests - self.total_errors) / max(self.total_requests, 1) * 100
        }
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.browser:
            await self.browser.close()

# Глобальный экземпляр
antiban_system = AdvancedAntiBan() 