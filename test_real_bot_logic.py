#!/usr/bin/env python3
"""
Тест реальной логики бота
"""

import requests
import logging
import Config
import time
import random
from vinted_scanner import vinted_antiblock
from advanced_antiban import advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_real_bot_logic():
    """Тест реальной логики бота"""
    print("🧪 ТЕСТ РЕАЛЬНОЙ ЛОГИКИ БОТА:")
    print("=" * 50)
    
    # 1. Получаем session и headers как в боте
    session = requests.Session()
    headers = vinted_antiblock.get_headers()
    
    # 2. Получаем cookies как в боте
    print("🔧 Получаем cookies...")
    session.post(Config.vinted_url, headers=headers, timeout=30)
    cookies = session.cookies.get_dict()
    print(f"🍪 Cookies: {cookies}")
    
    # 3. Тестируем с реальными параметрами бота
    topic_data = Config.topics["bags"]
    params = topic_data["query"]
    print(f"📋 Params: {params}")
    
    # 4. Тестируем продвинутую систему
    print("\n🚀 ТЕСТ ПРОДВИНУТОЙ СИСТЕМЫ:")
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    try:
        result = advanced_system.make_http_request(url, params, cookies)
        print(f"📊 Результат: {result is not None}")
        if result:
            print(f"📦 Найдено товаров: {len(result.get('items', []))}")
        else:
            print("❌ Нет данных")
            
        print(f"📊 HTTP requests: {advanced_system.http_requests}")
        print(f"📊 HTTP success: {advanced_system.http_success}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 5. Тестируем базовую систему для сравнения
    print("\n🛡️ ТЕСТ БАЗОВОЙ СИСТЕМЫ:")
    try:
        response = requests.get(
            url, 
            params=params, 
            cookies=cookies, 
            headers=headers,
            timeout=30
        )
        print(f"📊 Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Найдено товаров: {len(data.get('items', []))}")
        else:
            print(f"❌ Ошибка: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_real_bot_logic() 