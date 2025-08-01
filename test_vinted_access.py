#!/usr/bin/env python3
"""
Тест доступа к Vinted разными методами
"""

import requests
import time
import random

def test_vinted_access():
    """Тестируем доступ к Vinted"""
    print("🌐 ТЕСТ ДОСТУПА К VINTED")
    print("=" * 40)
    
    # Тест 1: Простой запрос
    print(f"\n📋 ТЕСТ 1: Простой запрос")
    print("-" * 20)
    
    try:
        response = requests.get("https://www.vinted.de", timeout=10)
        print(f"   Статус: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)[:3]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 2: С User-Agent
    print(f"\n📋 ТЕСТ 2: С User-Agent")
    print("-" * 20)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get("https://www.vinted.de", headers=headers, timeout=10)
        print(f"   Статус: {response.status_code}")
        print(f"   Cookies: {len(response.cookies)}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 3: Через сессию
    print(f"\n📋 ТЕСТ 3: Через сессию")
    print("-" * 20)
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get("https://www.vinted.de", timeout=10)
        print(f"   Статус: {response.status_code}")
        print(f"   Cookies: {len(session.cookies)}")
        
        if session.cookies:
            print(f"   Cookie names: {list(session.cookies.keys())}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 4: API запрос
    print(f"\n📋 ТЕСТ 4: API запрос")
    print("-" * 20)
    
    api_params = {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '',
        'order': 'newest_first',
        'price_to': '50'
    }
    
    try:
        response = session.get("https://www.vinted.de/api/v2/catalog/items", params=api_params, timeout=10)
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API доступен, получено данных: {len(data.get('items', []))}")
        else:
            print(f"   ❌ API недоступен: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Ошибка API: {str(e)[:50]}")
    
    # Тест 5: С задержкой
    print(f"\n📋 ТЕСТ 5: С задержкой")
    print("-" * 20)
    
    time.sleep(2)
    
    try:
        response = session.get("https://www.vinted.de", timeout=10)
        print(f"   Статус: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    print(f"\n✅ ТЕСТ ДОСТУПА ЗАВЕРШЕН")

if __name__ == "__main__":
    test_vinted_access() 