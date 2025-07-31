#!/usr/bin/env python3
"""
Тест счетчиков продвинутой системы
"""

import logging
import Config
from advanced_antiban import advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_counters():
    """Тест счетчиков"""
    print("🧪 ТЕСТ СЧЕТЧИКОВ:")
    print("=" * 30)
    
    # Проверяем начальные значения
    stats1 = advanced_system.get_stats()
    print(f"📊 Начальные счетчики:")
    print(f"   HTTP requests: {stats1['http_requests']}")
    print(f"   HTTP success: {stats1['http_success']}")
    print(f"   Browser requests: {stats1['browser_requests']}")
    print(f"   Browser success: {stats1['browser_success']}")
    
    # Делаем тестовый запрос
    print("\n🚀 Делаем тестовый запрос...")
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    params = {'page': '1', 'per_page': '2'}
    
    result = advanced_system.make_http_request(url, params)
    print(f"📊 Результат: {result is not None}")
    
    # Проверяем счетчики после запроса
    stats2 = advanced_system.get_stats()
    print(f"\n📊 Счетчики после запроса:")
    print(f"   HTTP requests: {stats2['http_requests']}")
    print(f"   HTTP success: {stats2['http_success']}")
    print(f"   Browser requests: {stats2['browser_requests']}")
    print(f"   Browser success: {stats2['browser_success']}")
    
    # Проверяем что счетчики изменились
    if stats2['http_requests'] > stats1['http_requests']:
        print("✅ HTTP requests увеличился")
    else:
        print("❌ HTTP requests не изменился")
        
    if stats2['http_success'] > stats1['http_success']:
        print("✅ HTTP success увеличился")
    else:
        print("❌ HTTP success не изменился")

if __name__ == "__main__":
    test_counters() 