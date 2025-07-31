#!/usr/bin/env python3
"""
Тест с cookies для решения 401 ошибки
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
    scan_topic, list_analyzed_items
)
from advanced_antiban import get_advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_vinted_cookies():
    """Получение cookies от Vinted"""
    print("\n🍪 ПОЛУЧЕНИЕ COOKIES ОТ VINTED:")
    print("=" * 40)
    
    try:
        # Создаем сессию
        session = requests.Session()
        
        # Получаем заголовки
        headers = vinted_antiblock.get_headers()
        print(f"📋 Заголовки: {headers}")
        
        # Делаем запрос на главную страницу для получения cookies
        print(f"🌐 Запрос к главной странице: {Config.vinted_url}")
        response = session.get(Config.vinted_url, headers=headers, timeout=30)
        
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            cookies = session.cookies.get_dict()
            print(f"✅ Cookies получены: {cookies}")
            return cookies
        else:
            print(f"❌ Ошибка получения cookies: {response.status_code}")
            print(f"📝 Ответ: {response.text[:200]}")
            return {}
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return {}

def test_basic_system_with_cookies():
    """Тест базовой системы с cookies"""
    print("\n🔍 ТЕСТ БАЗОВОЙ СИСТЕМЫ С COOKIES:")
    print("=" * 50)
    
    # Получаем cookies
    cookies = get_vinted_cookies()
    if not cookies:
        print("❌ Не удалось получить cookies")
        return False
    
    # Получаем заголовки
    headers = vinted_antiblock.get_headers()
    
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
    print(f"🍪 Cookies: {cookies}")
    
    try:
        # Делаем запрос с cookies
        response = requests.get(url, params=test_params, headers=headers, cookies=cookies, timeout=30)
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

def test_advanced_system_with_cookies():
    """Тест продвинутой системы с cookies"""
    print("\n🚀 ТЕСТ ПРОДВИНУТОЙ СИСТЕМЫ С COOKIES:")
    print("=" * 50)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Получаем cookies
    cookies = get_vinted_cookies()
    if not cookies:
        print("❌ Не удалось получить cookies")
        return False
    
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
    print(f"🍪 Cookies: {cookies}")
    
    try:
        # Делаем запрос через продвинутую систему с cookies
        data = advanced_system.make_http_request(url, test_params, cookies)
        
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

def test_proxy_with_cookies():
    """Тест прокси с cookies"""
    print("\n📡 ТЕСТ ПРОКСИ С COOKIES:")
    print("=" * 40)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Получаем cookies
    cookies = get_vinted_cookies()
    if not cookies:
        print("❌ Не удалось получить cookies")
        return False
    
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
    print(f"🍪 Cookies: {cookies}")
    
    try:
        # Делаем запрос через прокси с cookies
        data = advanced_system.make_http_request(url, test_params, cookies)
        
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

def test_session_cookies():
    """Тест сессионных cookies"""
    print("\n🔄 ТЕСТ СЕССИОННЫХ COOKIES:")
    print("=" * 40)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Создаем сессию
    session = requests.Session()
    
    # Получаем cookies через сессию
    headers = vinted_antiblock.get_headers()
    print("🌐 Получаем cookies через сессию...")
    
    try:
        response = session.get(Config.vinted_url, headers=headers, timeout=30)
        cookies = session.cookies.get_dict()
        print(f"🍪 Сессионные cookies: {cookies}")
        
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
        
        # Делаем запрос через сессию
        response = session.get(url, params=test_params, timeout=30)
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items_count = len(data.get('items', []))
            print(f"✅ УСПЕХ С СЕССИЕЙ: Найдено {items_count} товаров")
            return True
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"📝 Ответ: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_multiple_requests_with_cookies():
    """Тест множественных запросов с cookies"""
    print("\n🔄 ТЕСТ МНОЖЕСТВЕННЫХ ЗАПРОСОВ С COOKIES:")
    print("=" * 55)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return False
        
    advanced_system = get_advanced_system()
    
    # Получаем cookies
    cookies = get_vinted_cookies()
    if not cookies:
        print("❌ Не удалось получить cookies")
        return False
    
    # Тестовые топики
    test_topics = [
        {
            'name': 'bags',
            'params': {
                'page': '1',
                'per_page': '2',
                'search_text': '',
                'catalog_ids': '',
                'brand_ids': '212366',
                'order': 'newest_first',
                'price_to': '45'
            }
        },
        {
            'name': 'bags 2',
            'params': {
                'page': '1',
                'per_page': '2',
                'search_text': 'ggl',
                'catalog_ids': '19,82',
                'brand_ids': '',
                'order': 'newest_first',
                'price_to': '45'
            }
        }
    ]
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    
    for i, topic in enumerate(test_topics, 1):
        print(f"\n🔍 Запрос {i}: {topic['name']}")
        print("-" * 30)
        
        try:
            data = advanced_system.make_http_request(url, topic['params'], cookies)
            
            if data:
                items_count = len(data.get('items', []))
                print(f"✅ Найдено {items_count} товаров")
                
                # Показываем первый товар
                if data.get('items'):
                    item = data['items'][0]
                    print(f"   📦 {item.get('title', 'N/A')} - {item.get('price', {}).get('amount', 'N/A')} {item.get('price', {}).get('currency_code', '')}")
            else:
                print("❌ Нет данных")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        # Небольшая задержка между запросами
        time.sleep(1)
    
    return True

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ С COOKIES")
    print("=" * 35)
    
    results = {
        'basic_with_cookies': False,
        'advanced_with_cookies': False,
        'proxy_with_cookies': False,
        'session_cookies': False,
        'multiple_requests': False
    }
    
    try:
        # Тест базовой системы с cookies
        results['basic_with_cookies'] = test_basic_system_with_cookies()
        
        # Тест продвинутой системы с cookies
        results['advanced_with_cookies'] = test_advanced_system_with_cookies()
        
        # Тест прокси с cookies
        results['proxy_with_cookies'] = test_proxy_with_cookies()
        
        # Тест сессионных cookies
        results['session_cookies'] = test_session_cookies()
        
        # Тест множественных запросов
        results['multiple_requests'] = test_multiple_requests_with_cookies()
        
        # Итоговая статистика
        print("\n📊 ИТОГОВАЯ СТАТИСТИКА С COOKIES:")
        print("=" * 45)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test}: {status}")
        
        print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ С COOKIES ПРОЙДЕНЫ!")
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