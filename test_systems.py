#!/usr/bin/env python3
"""
Тест для сравнения базовой и продвинутой систем
"""

import requests
import logging
import Config
from vinted_scanner import vinted_antiblock
from advanced_antiban import advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_basic_system():
    """Тест базовой системы"""
    print("\n🔍 ТЕСТ БАЗОВОЙ СИСТЕМЫ:")
    print("=" * 50)
    
    # Получаем заголовки базовой системы
    basic_headers = vinted_antiblock.get_headers()
    print(f"📋 Заголовки базовой системы:")
    for key, value in basic_headers.items():
        print(f"   {key}: {value}")
    
    # Тестовый запрос
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    params = {'page': '1', 'per_page': '2'}
    
    print(f"\n🌐 URL: {url}")
    print(f"📋 Параметры: {params}")
    
    try:
        response = requests.get(url, params=params, headers=basic_headers, timeout=30)
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ УСПЕХ: Найдено {len(data.get('items', []))} товаров")
            return True
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_advanced_system():
    """Тест продвинутой системы"""
    print("\n🚀 ТЕСТ ПРОДВИНУТОЙ СИСТЕМЫ:")
    print("=" * 50)
    
    # Получаем заголовки продвинутой системы
    advanced_headers = advanced_system.get_random_headers()
    print(f"📋 Заголовки продвинутой системы:")
    for key, value in advanced_headers.items():
        print(f"   {key}: {value}")
    
    # Тестовый запрос
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    params = {'page': '1', 'per_page': '2'}
    
    print(f"\n🌐 URL: {url}")
    print(f"📋 Параметры: {params}")
    
    try:
        # Используем сессию продвинутой системы
        response = advanced_system.session.get(
            url, 
            params=params, 
            headers=advanced_headers, 
            timeout=30
        )
        print(f"📊 Статус: {response.status_code}")
        print(f"📋 Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ УСПЕХ: Найдено {len(data.get('items', []))} товаров")
            return True
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_direct_comparison():
    """Прямое сравнение запросов"""
    print("\n⚖️ ПРЯМОЕ СРАВНЕНИЕ:")
    print("=" * 50)
    
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    params = {'page': '1', 'per_page': '2'}
    
    # Базовая система
    basic_headers = vinted_antiblock.get_headers()
    basic_response = requests.get(url, params=params, headers=basic_headers, timeout=30)
    
    # Продвинутая система  
    advanced_headers = advanced_system.get_random_headers()
    advanced_response = advanced_system.session.get(url, params=params, headers=advanced_headers, timeout=30)
    
    print(f"📊 Базовая система: {basic_response.status_code}")
    print(f"📊 Продвинутая система: {advanced_response.status_code}")
    
    print(f"\n📋 Различия в заголовках:")
    basic_keys = set(basic_headers.keys())
    advanced_keys = set(advanced_headers.keys())
    
    print(f"   Только в базовой: {basic_keys - advanced_keys}")
    print(f"   Только в продвинутой: {advanced_keys - basic_keys}")
    print(f"   Общие: {basic_keys & advanced_keys}")
    
    # Сравниваем общие заголовки
    for key in basic_keys & advanced_keys:
        if basic_headers[key] != advanced_headers[key]:
            print(f"   🔄 {key}:")
            print(f"      Базовая: {basic_headers[key]}")
            print(f"      Продвинутая: {advanced_headers[key]}")

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМ АНТИБАНА")
    print("=" * 60)
    
    # Тест базовой системы
    basic_success = test_basic_system()
    
    # Тест продвинутой системы
    advanced_success = test_advanced_system()
    
    # Прямое сравнение
    test_direct_comparison()
    
    # Результаты
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("=" * 30)
    print(f"✅ Базовая система: {'РАБОТАЕТ' if basic_success else 'НЕ РАБОТАЕТ'}")
    print(f"🚀 Продвинутая система: {'РАБОТАЕТ' if advanced_success else 'НЕ РАБОТАЕТ'}")
    
    if basic_success and not advanced_success:
        print("\n🔍 ВЫВОД: Базовая система работает, продвинутая блокируется")
        print("💡 Возможные причины:")
        print("   - Разные User-Agent")
        print("   - Разные заголовки")
        print("   - Разные сессии")
        print("   - Vinted детектит продвинутую систему")

if __name__ == "__main__":
    main() 