#!/usr/bin/env python3
"""
Быстрая оптимизированная антибан система
"""

import random
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests
from fake_useragent import UserAgent

@dataclass
class SessionData:
    """Данные сессии"""
    headers: Dict
    user_agent: str
    requests_count: int = 0
    errors_count: int = 0
    last_success: float = 0

class FastAntiBan:
    """Быстрая антибан система"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.current_session = self._create_session()
        self.session_rotation_count = 0
        
        # Статистика
        self.total_requests = 0
        self.total_errors = 0
        self.total_blocks = 0
        self.success_count = 0
        
        # Настройки - максимально агрессивные для скорости
        self.max_requests_per_session = 50
        self.max_errors_per_session = 10
        self.base_delay = (0.05, 0.1)  # Минимальные задержки
        self.error_delay = (0.1, 0.2)  # Очень короткие задержки при ошибках
    
    def _create_session(self) -> SessionData:
        """Создание новой сессии"""
        return SessionData(
            headers=self._generate_headers(),
            user_agent=self.ua.random
        )
    
    def _generate_headers(self) -> Dict:
        """Генерация реалистичных заголовков"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.vinted.de/",
            "Origin": "https://www.vinted.de",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }
    
    def _rotate_session(self):
        """Быстрая ротация сессии"""
        self.current_session = self._create_session()
        self.session_rotation_count += 1
        logging.info(f"🔄 Ротация сессии #{self.session_rotation_count}")
    
    def _handle_error(self, status_code: int = None):
        """Быстрая обработка ошибок"""
        self.current_session.errors_count += 1
        self.total_errors += 1
        
        # Считаем блокировки
        if status_code in [403, 429, 503, 521]:
            self.total_blocks += 1
            logging.warning(f"🚫 Блокировка {status_code}")
        
        # Быстрая ротация при превышении лимитов
        if (self.current_session.errors_count >= self.max_errors_per_session or 
            self.current_session.requests_count >= self.max_requests_per_session):
            self._rotate_session()
        
        # Короткая пауза при ошибках
        delay = random.uniform(*self.error_delay)
        time.sleep(delay)
    
    def smart_request(self, url: str, params: Dict = None) -> Tuple[Optional[Dict], bool]:
        """Быстрый умный запрос"""
        try:
            # Минимальная задержка для скорости
            delay = random.uniform(*self.base_delay)
            time.sleep(delay)
            
            # Выполняем запрос
            response = requests.get(
                url,
                params=params,
                headers=self.current_session.headers,
                timeout=10  # Быстрый таймаут
            )
            
            self.current_session.requests_count += 1
            self.total_requests += 1
            
            if response.status_code == 200:
                self.current_session.last_success = time.time()
                self.success_count += 1
                
                try:
                    data = response.json()
                    return data, True
                except:
                    return {"status": "ok"}, True
                    
            else:
                self._handle_error(response.status_code)
                return None, False
                
        except Exception as e:
            self._handle_error()
            logging.error(f"❌ Ошибка запроса: {str(e)[:30]}")
            return None, False
    
    def get_vinted_items(self, search_params: Dict) -> Optional[Dict]:
        """Быстрое получение товаров с Vinted"""
        url = "https://www.vinted.de/api/v2/catalog/items"
        
        # Добавляем параметры для маскировки
        params = search_params.copy()
        params["_t"] = int(time.time() * 1000)
        params["_r"] = random.randint(1000, 9999)
        
        result, success = self.smart_request(url, params)
        
        if success and result:
            items_count = len(result.get('items', []))
            logging.info(f"✅ Получено {items_count} товаров")
            return result
        else:
            return None
    
    def get_stats(self) -> Dict:
        """Статистика системы"""
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_blocks": self.total_blocks,
            "success_count": self.success_count,
            "session_rotations": self.session_rotation_count,
            "success_rate": (self.success_count / max(self.total_requests, 1)) * 100
        }

# Глобальный экземпляр
fast_antiban_system = FastAntiBan()