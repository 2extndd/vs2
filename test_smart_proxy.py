#!/usr/bin/env python3
"""
Тест умной системы прокси
"""

import sys
import time
import random
from datetime import datetime
sys.path.append('.')

import Config
from advanced_antiban import get_advanced_system

def test_smart_proxy_system():
    """Тест умной системы прокси"""
    print("🧪 ТЕСТ УМНОЙ СИСТЕМЫ ПРОКСИ")
    print("=" * 50)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Получаем систему
    system = get_advanced_system()
    
    print(f"📊 Загружено прокси: {len(system.proxies)}")
    print(f"🧠 Режим прокси: {system.proxy_mode}")
    print(f"🔧 Использует прокси: {system._should_use_proxy()}")
    
    # Тестируем несколько запросов
    test_params = [
        {
            'name': 'Prada',
            'params': {
                'page': '1', 'per_page': '2', 'search_text': '',
                'catalog_ids': '2050,1231,82', 'brand_ids': '3573',
                'order': 'newest_first', 'price_to': '80'
            }
        },
        {
            'name': 'bags',
            'params': {
                'page': '1', 'per_page': '2', 'search_text': '',
                'catalog_ids': '', 'brand_ids': '212366',
                'order': 'newest_first', 'price_to': '45'
            }
        }
    ]
    
    successful_tests = 0
    total_tests = 0
    
    for i, test_case in enumerate(test_params, 1):
        print(f"\n--- Тест {i}/{len(test_params)}: {test_case['name']} ---")
        
        # Проверяем состояние прокси перед запросом
        print(f"🧠 Режим прокси: {system.proxy_mode}")
        print(f"🔧 Использует прокси: {system._should_use_proxy()}")
        if system.current_proxy:
            print(f"📡 Текущий прокси: {system.current_proxy['host']}:{system.current_proxy['port']}")
        
        start_time = time.time()
        url = f"{Config.vinted_url}/api/v2/catalog/items"
        
        try:
            result = system.make_http_request(url, test_case['params'])
            response_time = time.time() - start_time
            
            if result:
                items = result.get('items', [])
                print(f"✅ УСПЕХ: {len(items)} товаров за {response_time:.2f}s")
                successful_tests += 1
                
                if items:
                    for j, item in enumerate(items[:2], 1):
                        title = item.get('title', 'N/A')
                        price = item.get('price', {})
                        amount = price.get('amount', 'N/A')
                        currency = price.get('currency_code', '')
                        print(f"   {j}. {title} - {amount} {currency}")
            else:
                print(f"❌ ОШИБКА: Нет данных за {response_time:.2f}s")
                
        except Exception as e:
            print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
            
        total_tests += 1
        
        # Пауза между тестами
        if i < len(test_params):
            delay = random.uniform(2, 4)
            print(f"⏱️ Пауза {delay:.1f}s...")
            time.sleep(delay)
    
    # Статистика
    stats = system.get_stats()
    print(f"\n📊 РЕЗУЛЬТАТЫ УМНОЙ СИСТЕМЫ ПРОКСИ:")
    print(f"✅ Успешных тестов: {successful_tests}/{total_tests}")
    print(f"📊 Успешность: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "📊 Успешность: 0%")
    print(f"📊 HTTP запросы: {stats['http_success']}/{stats['http_requests']}")
    print(f"📈 Общая успешность: {stats['success_rate']:.1f}%")
    print(f"📡 Прокси: {stats['proxies_count']} активных")
    print(f"⚠️ Ошибок подряд: {stats['consecutive_errors']}")
    
    # Новая статистика прокси
    print(f"\n🧠 УМНАЯ СИСТЕМА ПРОКСИ:")
    print(f"📊 Режим прокси: {stats['proxy_mode']}")
    print(f"✅ Успехов прокси: {stats['proxy_successes']}")
    print(f"❌ Ошибок прокси: {stats['proxy_failures']}")
    print(f"🔧 Использует прокси: {'Да' if stats['should_use_proxy'] else 'Нет'}")
    
    # Статистика прокси
    if stats.get('proxy_stats'):
        print(f"\n📊 СТАТИСТИКА ПРОКСИ:")
        for proxy, proxy_stat in stats['proxy_stats'].items():
            if proxy_stat['requests'] > 0:
                print(f"   • {proxy}: {proxy_stat['success']}/{proxy_stat['requests']} ({proxy_stat['success_rate']:.1f}%)")
    
    print(f"\n✅ ТЕСТ УМНОЙ СИСТЕМЫ ПРОКСИ ЗАВЕРШЕН!")
    print(f"🕐 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_smart_proxy_system() 