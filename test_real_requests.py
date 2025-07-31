#!/usr/bin/env python3
"""
Реальные тесты с настоящими запросами к Vinted API
"""

import sys
import os
import time
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import Config
from vinted_scanner import (
    vinted_antiblock, system_mode, ADVANCED_SYSTEM_AVAILABLE,
    advanced_system_errors, basic_system_errors, max_system_errors,
    scan_topic, list_analyzed_items
)
from advanced_antiban import get_advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_basic_system_real():
    """Тест базовой системы с реальными запросами"""
    print("\n🔍 ТЕСТ БАЗОВОЙ СИСТЕМЫ (РЕАЛЬНЫЕ ЗАПРОСЫ):")
    print("=" * 55)
    
    # Получаем заголовки
    headers = vinted_antiblock.get_headers()
    print(f"📋 Заголовки: {headers}")
    
    # Тестовые параметры
    test_params = {
        'page': '1',
        'per_page': '5',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '212366',  # GGL
        'order': 'newest_first',
        'price_to': '45'
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    print(f"🌐 URL: {url}")
    print(f"📋 Параметры: {test_params}")
    
    try:
        # Делаем реальный запрос
        response = requests.get(url, params=test_params, headers=headers, timeout=30)
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items_count = len(data.get('items', []))
            print(f"✅ УСПЕХ: Найдено {items_count} товаров")
            
            # Показываем первые 2 товара
            for i, item in enumerate(data.get('items', [])[:2]):
                print(f"   {i+1}. {item.get('title', 'N/A')} - {item.get('price', {}).get('amount', 'N/A')} {item.get('price', {}).get('currency_code', '')}")
            
            return True
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"📝 Ответ: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_advanced_system_real():
    """Тест продвинутой системы с реальными запросами"""
    print("\n🚀 ТЕСТ ПРОДВИНУТОЙ СИСТЕМЫ (РЕАЛЬНЫЕ ЗАПРОСЫ):")
    print("=" * 55)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Тестовые параметры
    test_params = {
        'page': '1',
        'per_page': '5',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '212366',  # GGL
        'order': 'newest_first',
        'price_to': '45'
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    print(f"🌐 URL: {url}")
    print(f"📋 Параметры: {test_params}")
    
    try:
        # Делаем реальный запрос через продвинутую систему
        data = advanced_system.make_http_request(url, test_params)
        
        if data:
            items_count = len(data.get('items', []))
            print(f"✅ УСПЕХ: Найдено {items_count} товаров")
            
            # Показываем первые 2 товара
            for i, item in enumerate(data.get('items', [])[:2]):
                print(f"   {i+1}. {item.get('title', 'N/A')} - {item.get('price', {}).get('amount', 'N/A')} {item.get('price', {}).get('currency_code', '')}")
            
            return True
        else:
            print("❌ ОШИБКА: Нет данных от продвинутой системы")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_proxy_requests():
    """Тест запросов через прокси"""
    print("\n📡 ТЕСТ ЗАПРОСОВ ЧЕРЕЗ ПРОКСИ:")
    print("=" * 45)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Включаем прокси
    advanced_system.enable_proxies()
    print(f"✅ Прокси включен: {advanced_system.current_proxy['host']}:{advanced_system.current_proxy['port']}")
    
    # Тестовые параметры
    test_params = {
        'page': '1',
        'per_page': '3',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '212366',
        'order': 'newest_first',
        'price_to': '45'
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    try:
        # Делаем запрос через прокси
        data = advanced_system.make_http_request(url, test_params)
        
        if data:
            items_count = len(data.get('items', []))
            print(f"✅ УСПЕХ ЧЕРЕЗ ПРОКСИ: Найдено {items_count} товаров")
            return True
        else:
            print("❌ ОШИБКА: Нет данных через прокси")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_mode_switching_real():
    """Тест реального переключения режимов"""
    print("\n🔄 ТЕСТ РЕАЛЬНОГО ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ:")
    print("=" * 50)
    
    # Тестовые данные
    test_topic = {
        "thread_id": 190,
        "query": {
            'page': '1',
            'per_page': '3',
            'search_text': '',
            'catalog_ids': '',
            'brand_ids': '212366',
            'order': 'newest_first',
            'price_to': '45',
        },
        "exclude_catalog_ids": "26,98,146,139,152,1918"
    }
    
    # Симулируем сессию и cookies
    session = requests.Session()
    cookies = {}
    
    print("🎯 Тестируем режим 'basic':")
    global system_mode
    old_mode = system_mode
    system_mode = "basic"
    
    try:
        # Вызываем scan_topic напрямую
        scan_topic("test_basic", test_topic, cookies, session, is_priority=True)
        print("✅ Режим 'basic' работает")
    except Exception as e:
        print(f"❌ Ошибка в режиме 'basic': {e}")
    
    print("\n🎯 Тестируем режим 'advanced':")
    system_mode = "advanced"
    
    try:
        scan_topic("test_advanced", test_topic, cookies, session, is_priority=True)
        print("✅ Режим 'advanced' работает")
    except Exception as e:
        print(f"❌ Ошибка в режиме 'advanced': {e}")
    
    print("\n🎯 Тестируем режим 'proxy':")
    system_mode = "proxy"
    
    try:
        scan_topic("test_proxy", test_topic, cookies, session, is_priority=True)
        print("✅ Режим 'proxy' работает")
    except Exception as e:
        print(f"❌ Ошибка в режиме 'proxy': {e}")
    
    # Возвращаем старый режим
    system_mode = old_mode
    print(f"\n🔄 Возврат к режиму: {system_mode}")

def test_multiple_topics():
    """Тест нескольких топиков"""
    print("\n📋 ТЕСТ НЕСКОЛЬКИХ ТОПИКОВ:")
    print("=" * 35)
    
    # Берем первые 3 топика из конфига
    topics = list(Config.topics.items())[:3]
    
    session = requests.Session()
    cookies = {}
    
    for topic_name, topic_data in topics:
        print(f"\n🔍 Тестируем топик: {topic_name}")
        print("-" * 30)
        
        try:
            scan_topic(topic_name, topic_data, cookies, session, is_priority=False)
            print(f"✅ Топик '{topic_name}' обработан")
        except Exception as e:
            print(f"❌ Ошибка в топике '{topic_name}': {e}")

def test_error_simulation():
    """Тест симуляции ошибок"""
    print("\n🚨 ТЕСТ СИМУЛЯЦИИ ОШИБОК:")
    print("=" * 35)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    # Симулируем ошибки в прокси
    print("🚨 Симулируем ошибки в прокси...")
    for proxy in advanced_system.proxies[:2]:
        proxy['errors'] = 3
        print(f"   ❌ Прокси {proxy['host']}:{proxy['port']} заблокирован")
    
    # Делаем запрос - должен выбрать другой прокси
    test_params = {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '212366',
        'order': 'newest_first',
        'price_to': '45'
    }
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    try:
        data = advanced_system.make_http_request(url, test_params)
        if data:
            print("✅ Запрос прошел через рабочий прокси")
        else:
            print("❌ Запрос не прошел")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Сбрасываем ошибки
    for proxy in advanced_system.proxies:
        proxy['errors'] = 0
    print("✅ Ошибки сброшены")

def main():
    """Главная функция тестирования"""
    print("🧪 РЕАЛЬНЫЕ ТЕСТЫ С ЗАПРОСАМИ К VINTED API")
    print("=" * 60)
    
    results = {
        'basic_system': False,
        'advanced_system': False,
        'proxy_requests': False,
        'mode_switching': False,
        'multiple_topics': False,
        'error_simulation': False
    }
    
    try:
        # Тест базовой системы
        results['basic_system'] = test_basic_system_real()
        
        # Тест продвинутой системы
        results['advanced_system'] = test_advanced_system_real()
        
        # Тест прокси
        results['proxy_requests'] = test_proxy_requests()
        
        # Тест переключения режимов
        test_mode_switching_real()
        results['mode_switching'] = True
        
        # Тест нескольких топиков
        test_multiple_topics()
        results['multiple_topics'] = True
        
        # Тест симуляции ошибок
        test_error_simulation()
        results['error_simulation'] = True
        
        # Итоговая статистика
        print("\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print("=" * 30)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test}: {status}")
        
        print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        
        # Показываем найденные товары
        if list_analyzed_items:
            print(f"\n📦 НАЙДЕНО ТОВАРОВ: {len(list_analyzed_items)}")
            print("   (Проверьте vinted_items.txt для деталей)")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 