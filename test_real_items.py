#!/usr/bin/env python3
"""
Тест получения реальных товаров с Vinted
"""

import sys
import json
sys.path.append('.')

from advanced_antiban import get_advanced_system
import Config

def test_real_items():
    """Тестирование получения реальных товаров"""
    print("🧪 Тестирование получения реальных товаров...")
    
    system = get_advanced_system()
    
    # Тестируем топик Prada
    prada_params = {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '2050,1231,82',
        'brand_ids': '3573',
        'order': 'newest_first',
        'price_to': '80',
    }
    
    print(f"🔍 Параметры Prada: {prada_params}")
    print(f"🌐 URL: {Config.vinted_url}/api/v2/catalog/items")
    
    result = system.make_http_request(
        f"{Config.vinted_url}/api/v2/catalog/items",
        prada_params
    )
    
    if result:
        items = result.get('items', [])
        print(f"✅ Найдено товаров: {len(items)}")
        
        if items:
            print("\n📦 Примеры товаров Prada:")
            for i, item in enumerate(items[:3], 1):
                title = item.get('title', 'N/A')
                price = item.get('price', {})
                amount = price.get('amount', 'N/A')
                currency = price.get('currency_code', '')
                brand = item.get('brand_title', 'N/A')
                
                print(f"  {i}. {title}")
                print(f"     💰 {amount} {currency}")
                print(f"     🏷️ {brand}")
                print()
        else:
            print("❌ Товары не найдены")
    else:
        print("❌ Ошибка получения данных")
    
    print("\n" + "="*50)
    print("🧪 Тестирование топика bags...")
    
    # Тестируем топик bags
    bags_params = {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '212366',
        'order': 'newest_first',
        'price_to': '45',
    }
    
    print(f"🔍 Параметры bags: {bags_params}")
    
    result2 = system.make_http_request(
        f"{Config.vinted_url}/api/v2/catalog/items",
        bags_params
    )
    
    if result2:
        items2 = result2.get('items', [])
        print(f"✅ Найдено товаров bags: {len(items2)}")
        
        if items2:
            print("\n📦 Примеры товаров bags:")
            for i, item in enumerate(items2[:3], 1):
                title = item.get('title', 'N/A')
                price = item.get('price', {})
                amount = price.get('amount', 'N/A')
                currency = price.get('currency_code', '')
                brand = item.get('brand_title', 'N/A')
                
                print(f"  {i}. {title}")
                print(f"     💰 {amount} {currency}")
                print(f"     🏷️ {brand}")
                print()
        else:
            print("❌ Товары bags не найдены")
    else:
        print("❌ Ошибка получения данных bags")
    
    # Статистика
    stats = system.get_stats()
    print(f"📊 Общая статистика системы:")
    print(f"   Запросы: {stats['http_requests']}")
    print(f"   Успех: {stats['http_success']}")
    print(f"   Процент успеха: {stats['success_rate']:.1f}%")
    print(f"   Ошибки 403: {stats['errors_403']}")
    print(f"   Ошибки 429: {stats['errors_429']}")
    print(f"   Подряд ошибок: {stats['consecutive_errors']}")
    print(f"   Текущий прокси: {stats['current_proxy']}")
    
    # Проверяем структуру данных
    if result and result.get('items'):
        item = result['items'][0]
        print(f"\n🔍 Структура данных товара:")
        print(f"   ID: {item.get('id')}")
        print(f"   URL: {item.get('url', 'N/A')}")
        print(f"   Фото: {item.get('photo', {}).get('full_size_url', 'N/A')[:50]}...")
        print(f"   Размер: {item.get('size_title', 'N/A')}")
        print(f"   Видимость: {item.get('is_visible')}")

if __name__ == "__main__":
    test_real_items() 