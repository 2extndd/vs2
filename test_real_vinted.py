#!/usr/bin/env python3
"""
Комплексный тест системы на реальном Vinted
Проверяет переключение между режимами, прокси и получение товаров
"""

import time
import logging
import requests
import json
from advanced_antiban import get_advanced_system
import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def test_basic_vs_advanced_mode():
    """Тест переключения между базовым и продвинутым режимом"""
    print("🔄 ТЕСТ: БАЗОВЫЙ VS ПРОДВИНУТЫЙ РЕЖИМ")
    print("=" * 60)
    
    # Инициализация систем
    advanced_system = get_advanced_system()
    
    # Тестовые параметры для Vinted
    test_params = {
        "search_text": "nike",
        "catalog_ids": "",
        "color_ids": "",
        "brand_ids": "",
        "size_ids": "",
        "material_ids": "",
        "status_ids": "",
        "country_ids": "",
        "city_ids": "",
        "is_for_swap": "0",
        "price_from": "",
        "price_to": "",
        "currency": "EUR"
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    print(f"🌐 URL: {url}")
    print(f"🔧 Параметры: {test_params}")
    
    # Тест 1: Базовый режим (прямые запросы)
    print(f"\n📊 ТЕСТ 1: БАЗОВЫЙ РЕЖИМ")
    print("-" * 40)
    
    basic_success = 0
    basic_requests = 3
    
    for i in range(basic_requests):
        print(f"🔄 Базовый запрос {i+1}/{basic_requests}:")
        
        try:
            # Прямой запрос без продвинутой системы
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Connection": "keep-alive"
            }
            
            response = requests.get(url, params=test_params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items_count = len(data.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
                basic_success += 1
            else:
                print(f"❌ Ошибка HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(2)
    
    basic_success_rate = (basic_success / basic_requests * 100) if basic_requests > 0 else 0
    print(f"📊 Базовый режим: {basic_success}/{basic_requests} ({basic_success_rate:.1f}%)")
    
    # Тест 2: Продвинутый режим
    print(f"\n📊 ТЕСТ 2: ПРОДВИНУТЫЙ РЕЖИМ")
    print("-" * 40)
    
    advanced_success = 0
    advanced_requests = 3
    
    for i in range(advanced_requests):
        print(f"🔄 Продвинутый запрос {i+1}/{advanced_requests}:")
        
        try:
            result = advanced_system.make_http_request(url, test_params)
            
            if result:
                items_count = len(result.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
                advanced_success += 1
            else:
                print(f"❌ Ошибка запроса")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(2)
    
    advanced_success_rate = (advanced_success / advanced_requests * 100) if advanced_requests > 0 else 0
    print(f"📊 Продвинутый режим: {advanced_success}/{advanced_requests} ({advanced_success_rate:.1f}%)")
    
    # Сравнение результатов
    print(f"\n📊 СРАВНЕНИЕ РЕЖИМОВ:")
    print(f"• Базовый: {basic_success_rate:.1f}%")
    print(f"• Продвинутый: {advanced_success_rate:.1f}%")
    
    return basic_success_rate, advanced_success_rate

def test_proxy_vs_noproxy_mode():
    """Тест переключения между прокси и без прокси в продвинутом режиме"""
    print(f"\n🔄 ТЕСТ: ПРОКСИ VS БЕЗ ПРОКСИ")
    print("=" * 60)
    
    advanced_system = get_advanced_system()
    
    # Тестовые параметры
    test_params = {
        "search_text": "adidas",
        "catalog_ids": "",
        "color_ids": "",
        "brand_ids": "",
        "size_ids": "",
        "material_ids": "",
        "status_ids": "",
        "country_ids": "",
        "city_ids": "",
        "is_for_swap": "0",
        "price_from": "",
        "price_to": "",
        "currency": "EUR"
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    # Тест 1: Режим с прокси
    print(f"\n📊 ТЕСТ 1: РЕЖИМ С ПРОКСИ")
    print("-" * 40)
    
    # Принудительно включаем прокси
    advanced_system.proxy_mode = "enabled"
    advanced_system._rotate_proxy()
    
    proxy_success = 0
    proxy_requests = 3
    
    for i in range(proxy_requests):
        print(f"🔄 Запрос с прокси {i+1}/{proxy_requests}:")
        
        try:
            result = advanced_system.make_http_request(url, test_params)
            
            if result:
                items_count = len(result.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
                proxy_success += 1
            else:
                print(f"❌ Ошибка запроса")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(2)
    
    proxy_success_rate = (proxy_success / proxy_requests * 100) if proxy_requests > 0 else 0
    print(f"📊 Режим с прокси: {proxy_success}/{proxy_requests} ({proxy_success_rate:.1f}%)")
    
    # Тест 2: Режим без прокси
    print(f"\n📊 ТЕСТ 2: РЕЖИМ БЕЗ ПРОКСИ")
    print("-" * 40)
    
    # Принудительно отключаем прокси
    advanced_system.proxy_mode = "disabled"
    advanced_system.current_proxy = None
    
    noproxy_success = 0
    noproxy_requests = 3
    
    for i in range(noproxy_requests):
        print(f"🔄 Запрос без прокси {i+1}/{noproxy_requests}:")
        
        try:
            result = advanced_system.make_http_request(url, test_params)
            
            if result:
                items_count = len(result.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
                noproxy_success += 1
            else:
                print(f"❌ Ошибка запроса")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(2)
    
    noproxy_success_rate = (noproxy_success / noproxy_requests * 100) if noproxy_requests > 0 else 0
    print(f"📊 Режим без прокси: {noproxy_success}/{noproxy_requests} ({noproxy_success_rate:.1f}%)")
    
    # Сравнение результатов
    print(f"\n📊 СРАВНЕНИЕ РЕЖИМОВ ПРОКСИ:")
    print(f"• С прокси: {proxy_success_rate:.1f}%")
    print(f"• Без прокси: {noproxy_success_rate:.1f}%")
    
    return proxy_success_rate, noproxy_success_rate

def test_proxy_health():
    """Тест проверки здоровья прокси"""
    print(f"\n🔄 ТЕСТ: ПРОВЕРКА ЗДОРОВЬЯ ПРОКСИ")
    print("=" * 60)
    
    advanced_system = get_advanced_system()
    
    print(f"📊 Тестируем все прокси...")
    
    working_proxies = []
    failed_proxies = []
    
    for i, proxy in enumerate(advanced_system.proxies):
        print(f"🔄 Тест прокси {i+1}/{len(advanced_system.proxies)}: {proxy['host']}:{proxy['port']}")
        
        if advanced_system._test_proxy(proxy):
            working_proxies.append(f"{proxy['host']}:{proxy['port']}")
            if proxy not in advanced_system.proxy_whitelist:
                advanced_system.proxy_whitelist.append(proxy)
            print(f"✅ Работает")
        else:
            failed_proxies.append(f"{proxy['host']}:{proxy['port']}")
            if proxy not in advanced_system.proxy_blacklist:
                advanced_system.proxy_blacklist.append(proxy)
            print(f"❌ Не работает")
        
        time.sleep(1)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ ПРОКСИ:")
    print(f"✅ Рабочих прокси: {len(working_proxies)}")
    print(f"❌ Неисправных прокси: {len(failed_proxies)}")
    print(f"📋 Whitelist: {len(advanced_system.proxy_whitelist)}")
    print(f"🚫 Blacklist: {len(advanced_system.proxy_blacklist)}")
    
    if working_proxies:
        print(f"\n✅ РАБОЧИЕ ПРОКСИ:")
        for proxy in working_proxies[:10]:  # Показываем первые 10
            print(f"• {proxy}")
    
    if failed_proxies:
        print(f"\n❌ НЕИСПРАВНЫЕ ПРОКСИ:")
        for proxy in failed_proxies[:10]:  # Показываем первые 10
            print(f"• {proxy}")
    
    return len(working_proxies), len(failed_proxies)

def test_different_search_queries():
    """Тест получения товаров с разными запросами"""
    print(f"\n🔄 ТЕСТ: РАЗНЫЕ ПОИСКОВЫЕ ЗАПРОСЫ")
    print("=" * 60)
    
    advanced_system = get_advanced_system()
    
    # Разные поисковые запросы
    search_queries = [
        {"search_text": "nike", "description": "Nike товары"},
        {"search_text": "adidas", "description": "Adidas товары"},
        {"search_text": "bags", "description": "Сумки"},
        {"search_text": "shoes", "description": "Обувь"},
        {"search_text": "dress", "description": "Платья"}
    ]
    
    results = {}
    
    for query in search_queries:
        print(f"\n🔍 Поиск: {query['description']} ('{query['search_text']}')")
        print("-" * 40)
        
        test_params = {
            "search_text": query['search_text'],
            "catalog_ids": "",
            "color_ids": "",
            "brand_ids": "",
            "size_ids": "",
            "material_ids": "",
            "status_ids": "",
            "country_ids": "",
            "city_ids": "",
            "is_for_swap": "0",
            "price_from": "",
            "price_to": "",
            "currency": "EUR"
        }
        
        url = f"{Config.vinted_url}/api/v2/catalog/items"
        
        try:
            result = advanced_system.make_http_request(url, test_params)
            
            if result:
                items_count = len(result.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
                
                # Показываем первые 3 товара
                if items_count > 0:
                    print(f"📋 ПЕРВЫЕ ТОВАРЫ:")
                    for i, item in enumerate(result['items'][:3]):
                        title = item.get('title', 'Без названия')
                        price = item.get('price', 'Цена не указана')
                        print(f"  {i+1}. {title} - {price}")
                
                results[query['search_text']] = {
                    'success': True,
                    'items_count': items_count
                }
            else:
                print(f"❌ Ошибка запроса")
                results[query['search_text']] = {
                    'success': False,
                    'items_count': 0
                }
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            results[query['search_text']] = {
                'success': False,
                'items_count': 0
            }
        
        time.sleep(3)
    
    # Итоговая статистика
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ПОИСКА:")
    total_success = 0
    total_items = 0
    
    for query, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {query}: {result['items_count']} товаров")
        if result['success']:
            total_success += 1
            total_items += result['items_count']
    
    success_rate = (total_success / len(search_queries) * 100) if search_queries else 0
    print(f"\n📊 Общая успешность: {success_rate:.1f}%")
    print(f"📊 Всего товаров найдено: {total_items}")
    
    return results

def test_auto_mode_switching():
    """Тест автоматического переключения режимов"""
    print(f"\n🔄 ТЕСТ: АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ")
    print("=" * 60)
    
    advanced_system = get_advanced_system()
    
    # Устанавливаем автоматический режим
    advanced_system.proxy_mode = "auto"
    
    print(f"📊 Начальный режим: {advanced_system.proxy_mode}")
    print(f"📊 Использует прокси: {advanced_system._should_use_proxy()}")
    
    # Делаем несколько запросов и наблюдаем за переключениями
    test_params = {
        "search_text": "test",
        "catalog_ids": "",
        "color_ids": "",
        "brand_ids": "",
        "size_ids": "",
        "material_ids": "",
        "status_ids": "",
        "country_ids": "",
        "city_ids": "",
        "is_for_swap": "0",
        "price_from": "",
        "price_to": "",
        "currency": "EUR"
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    mode_changes = []
    
    for i in range(5):
        print(f"\n🔄 Автоматический запрос {i+1}/5:")
        
        initial_mode = advanced_system.proxy_mode
        initial_use_proxy = advanced_system._should_use_proxy()
        
        try:
            result = advanced_system.make_http_request(url, test_params)
            
            final_mode = advanced_system.proxy_mode
            final_use_proxy = advanced_system._should_use_proxy()
            
            if initial_mode != final_mode or initial_use_proxy != final_use_proxy:
                mode_changes.append({
                    'request': i+1,
                    'initial_mode': initial_mode,
                    'final_mode': final_mode,
                    'initial_use_proxy': initial_use_proxy,
                    'final_use_proxy': final_use_proxy
                })
                print(f"🔄 ПЕРЕКЛЮЧЕНИЕ РЕЖИМА!")
                print(f"  Было: {initial_mode} (прокси: {initial_use_proxy})")
                print(f"  Стало: {final_mode} (прокси: {final_use_proxy})")
            else:
                print(f"📊 Режим не изменился: {final_mode} (прокси: {final_use_proxy})")
            
            if result:
                items_count = len(result.get('items', []))
                print(f"✅ Успех! Найдено товаров: {items_count}")
            else:
                print(f"❌ Ошибка запроса")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(3)
    
    print(f"\n📊 СТАТИСТИКА ПЕРЕКЛЮЧЕНИЙ:")
    print(f"• Всего переключений: {len(mode_changes)}")
    
    for change in mode_changes:
        print(f"• Запрос {change['request']}: {change['initial_mode']} → {change['final_mode']}")
    
    return mode_changes

def main():
    """Основная функция тестирования"""
    print("🧠 КОМПЛЕКСНЫЙ ТЕСТ СИСТЕМЫ НА РЕАЛЬНОМ VINTED")
    print("=" * 80)
    
    try:
        # Тест 1: Базовый vs Продвинутый режим
        basic_rate, advanced_rate = test_basic_vs_advanced_mode()
        
        # Тест 2: Прокси vs Без прокси
        proxy_rate, noproxy_rate = test_proxy_vs_noproxy_mode()
        
        # Тест 3: Проверка здоровья прокси
        working_proxies, failed_proxies = test_proxy_health()
        
        # Тест 4: Разные поисковые запросы
        search_results = test_different_search_queries()
        
        # Тест 5: Автоматическое переключение режимов
        mode_changes = test_auto_mode_switching()
        
        # Финальная статистика
        print(f"\n🎉 ФИНАЛЬНАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        print(f"📊 СРАВНЕНИЕ РЕЖИМОВ:")
        print(f"• Базовый: {basic_rate:.1f}%")
        print(f"• Продвинутый: {advanced_rate:.1f}%")
        
        print(f"\n📊 СРАВНЕНИЕ ПРОКСИ:")
        print(f"• С прокси: {proxy_rate:.1f}%")
        print(f"• Без прокси: {noproxy_rate:.1f}%")
        
        print(f"\n📊 ПРОКСИ:")
        print(f"• Рабочих: {working_proxies}")
        print(f"• Неисправных: {failed_proxies}")
        
        print(f"\n📊 ПОИСКОВЫЕ ЗАПРОСЫ:")
        successful_searches = sum(1 for result in search_results.values() if result['success'])
        total_searches = len(search_results)
        search_success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
        print(f"• Успешных запросов: {successful_searches}/{total_searches} ({search_success_rate:.1f}%)")
        
        print(f"\n📊 АВТОМАТИЧЕСКИЕ ПЕРЕКЛЮЧЕНИЯ:")
        print(f"• Количество переключений: {len(mode_changes)}")
        
        print(f"\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        logging.error(f"Ошибка в тестах: {e}")

if __name__ == "__main__":
    main() 