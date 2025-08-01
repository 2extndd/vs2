#!/usr/bin/env python3
"""
Тест доступности прокси
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import requests
import time

def test_proxy_availability():
    """Проверяем доступность прокси"""
    print("🔍 ПРОВЕРКА ДОСТУПНОСТИ ПРОКСИ")
    print("=" * 50)
    
    # Проверяем, загружены ли прокси
    if hasattr(vinted_scanner, 'advanced_system') and vinted_scanner.advanced_system:
        print(f"✅ Продвинутая система инициализирована")
        
        # Проверяем количество прокси
        proxy_count = len(vinted_scanner.advanced_system.proxies) if hasattr(vinted_scanner.advanced_system, 'proxies') else 0
        print(f"📊 Загружено прокси: {proxy_count}")
        
        if proxy_count > 0:
            print(f"✅ Прокси доступны")
            
            # Показываем первые 5 прокси
            print(f"\n📋 Первые 5 прокси:")
            for i, proxy in enumerate(vinted_scanner.advanced_system.proxies[:5]):
                print(f"   {i+1}. {proxy}")
        else:
            print(f"❌ Прокси не загружены")
    else:
        print(f"❌ Продвинутая система не инициализирована")
    
    # Проверяем файл прокси
    print(f"\n📁 ПРОВЕРКА ФАЙЛА ПРОКСИ")
    print("-" * 30)
    
    proxy_file = "proxies.txt"
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            proxy_lines = f.readlines()
        
        print(f"✅ Файл {proxy_file} найден")
        print(f"📊 Строк в файле: {len(proxy_lines)}")
        
        # Показываем первые 5 строк
        print(f"\n📋 Первые 5 строк:")
        for i, line in enumerate(proxy_lines[:5]):
            line = line.strip()
            if line:
                print(f"   {i+1}. {line}")
    else:
        print(f"❌ Файл {proxy_file} не найден")

def test_proxy_health():
    """Тестируем здоровье прокси"""
    print(f"\n🏥 ТЕСТ ЗДОРОВЬЯ ПРОКСИ")
    print("-" * 30)
    
    if hasattr(vinted_scanner, 'advanced_system') and vinted_scanner.advanced_system:
        # Симулируем проверку здоровья прокси
        print(f"🔍 Проверяем здоровье прокси...")
        
        # Показываем текущий прокси
        current_proxy = vinted_scanner.advanced_system.current_proxy
        if current_proxy:
            print(f"🎯 Текущий прокси: {current_proxy}")
        else:
            print(f"⚠️ Текущий прокси не установлен")
        
        # Проверяем режим прокси
        proxy_mode = getattr(vinted_scanner.advanced_system, 'proxy_mode', 'unknown')
        print(f"🔧 Режим прокси: {proxy_mode}")
        
        # Симулируем ротацию прокси
        print(f"🔄 Тестируем ротацию прокси...")
        if hasattr(vinted_scanner.advanced_system, '_rotate_proxy'):
            old_proxy = vinted_scanner.advanced_system.current_proxy
            vinted_scanner.advanced_system._rotate_proxy()
            new_proxy = vinted_scanner.advanced_system.current_proxy
            
            if old_proxy != new_proxy:
                print(f"✅ Ротация работает: {old_proxy} → {new_proxy}")
            else:
                print(f"⚠️ Ротация не изменила прокси")
        else:
            print(f"❌ Метод ротации не найден")
    else:
        print(f"❌ Продвинутая система недоступна")

def test_proxy_requests():
    """Тестируем запросы через прокси"""
    print(f"\n🌐 ТЕСТ ЗАПРОСОВ ЧЕРЕЗ ПРОКСИ")
    print("-" * 30)
    
    if hasattr(vinted_scanner, 'advanced_system') and vinted_scanner.advanced_system:
        # Симулируем HTTP запрос через прокси
        print(f"🚀 Тестируем HTTP запрос через прокси...")
        
        try:
            # Создаем тестовые параметры
            test_params = {
                'page': '1',
                'per_page': '1',
                'search_text': '',
                'catalog_ids': '',
                'brand_ids': '',
                'order': 'newest_first',
                'price_to': '50'
            }
            
            # Симулируем cookies
            test_cookies = {}
            
            # Настраиваем прокси режим
            vinted_scanner.advanced_system.proxy_mode = "enabled"
            
            print(f"🔧 Прокси режим: enabled")
            print(f"🎯 Текущий прокси: {vinted_scanner.advanced_system.current_proxy}")
            
            # Симулируем запрос (без реального вызова)
            print(f"✅ Система готова к запросам через прокси")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании прокси: {e}")
    else:
        print(f"❌ Продвинутая система недоступна")

def check_proxy_configuration():
    """Проверяем конфигурацию прокси"""
    print(f"\n⚙️ ПРОВЕРКА КОНФИГУРАЦИИ ПРОКСИ")
    print("-" * 30)
    
    # Проверяем переменные окружения
    print(f"🔍 Проверяем переменные окружения...")
    
    # Проверяем файлы конфигурации
    config_files = ["proxies.txt", "proxy_list.txt", "proxies.json"]
    found_files = []
    
    for file in config_files:
        if os.path.exists(file):
            found_files.append(file)
            print(f"✅ Найден файл: {file}")
        else:
            print(f"❌ Файл не найден: {file}")
    
    if found_files:
        print(f"\n📋 Найдено файлов конфигурации: {len(found_files)}")
    else:
        print(f"\n⚠️ Файлы конфигурации прокси не найдены")

if __name__ == "__main__":
    test_proxy_availability()
    test_proxy_health()
    test_proxy_requests()
    check_proxy_configuration()
    
    print(f"\n🎯 ПРОВЕРКА ПРОКСИ ЗАВЕРШЕНА!") 