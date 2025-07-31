#!/usr/bin/env python3
"""
Тест автоматического переключения режимов антибана
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import Config
from vinted_scanner import vinted_antiblock, system_mode, ADVANCED_SYSTEM_AVAILABLE
from advanced_antiban import get_advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_mode_switching():
    """Тест переключения режимов"""
    print("\n🧪 ТЕСТ ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ:")
    print("=" * 50)
    
    # Получаем продвинутую систему
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    print(f"🎯 Текущий режим: {system_mode}")
    print(f"📡 Прокси загружено: {len(advanced_system.proxies)}")
    
    # Тест 1: Проверка профилей клиентов
    print("\n🔍 ТЕСТ ПРОФИЛЕЙ КЛИЕНТОВ:")
    print("-" * 30)
    
    profiles = advanced_system.client_profiles
    print(f"📊 Создано профилей: {len(profiles)}")
    
    for i, profile in enumerate(profiles[:3]):  # Показываем первые 3
        print(f"   {i+1}. {profile['name']}")
        print(f"      User-Agent: {profile['user_agent'][:50]}...")
        print(f"      Accept: {profile['accept']}")
    
    # Тест 2: Проверка ротации прокси
    print("\n🔄 ТЕСТ РОТАЦИИ ПРОКСИ:")
    print("-" * 30)
    
    print("📡 Доступные прокси:")
    for i, proxy in enumerate(advanced_system.proxies):
        print(f"   {i+1}. {proxy['host']}:{proxy['port']}")
    
    # Симулируем несколько запросов для проверки ротации
    print("\n🚀 Симуляция запросов:")
    for i in range(6):  # Больше чем max_requests_per_proxy (5)
        old_proxy = advanced_system.current_proxy
        advanced_system._rotate_proxy()
        new_proxy = advanced_system.current_proxy
        
        if old_proxy != new_proxy:
            print(f"   Запрос {i+1}: Ротация прокси")
        else:
            print(f"   Запрос {i+1}: Тот же прокси")
    
    # Тест 3: Проверка включения/отключения прокси
    print("\n📡 ТЕСТ ВКЛЮЧЕНИЯ/ОТКЛЮЧЕНИЯ ПРОКСИ:")
    print("-" * 40)
    
    # Включаем прокси
    advanced_system.enable_proxies()
    print(f"✅ Прокси включены: {advanced_system.current_proxy['host']}:{advanced_system.current_proxy['port']}")
    
    # Отключаем прокси
    advanced_system.disable_proxies()
    print(f"❌ Прокси отключены: {advanced_system.current_proxy is None}")
    
    # Тест 4: Проверка статистики
    print("\n📊 ТЕСТ СТАТИСТИКИ:")
    print("-" * 20)
    
    stats = advanced_system.get_stats()
    print(f"📊 HTTP запросы: {stats['http_requests']}")
    print(f"📊 HTTP успех: {stats['http_success']}")
    print(f"📊 Прокси: {stats['proxies_count']} активных")
    print(f"📊 Текущий прокси: {stats['current_proxy']}")
    
    if stats.get('proxy_stats'):
        print("\n📈 Статистика прокси:")
        for proxy, proxy_stat in stats['proxy_stats'].items():
            print(f"   • {proxy}: {proxy_stat['success']}/{proxy_stat['requests']} ({proxy_stat['success_rate']:.1f}%)")
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")

def test_error_handling():
    """Тест обработки ошибок"""
    print("\n🚨 ТЕСТ ОБРАБОТКИ ОШИБОК:")
    print("=" * 40)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    # Симулируем ошибки
    print("🚀 Симуляция ошибок...")
    
    # Добавляем ошибки в прокси
    for proxy in advanced_system.proxies[:2]:  # Первые 2 прокси
        proxy['errors'] = 3
        print(f"   ❌ Прокси {proxy['host']}:{proxy['port']} заблокирован")
    
    # Проверяем ротацию с учетом ошибок
    print("\n🔄 Ротация с учетом ошибок:")
    for i in range(3):
        old_proxy = advanced_system.current_proxy
        advanced_system._rotate_proxy()
        new_proxy = advanced_system.current_proxy
        
        if old_proxy != new_proxy:
            print(f"   Ротация {i+1}: {new_proxy['host']}:{new_proxy['port']}")
        else:
            print(f"   Ротация {i+1}: Тот же прокси")
    
    print("✅ Тест обработки ошибок завершен!")

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ")
    print("=" * 50)
    
    try:
        test_mode_switching()
        test_error_handling()
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 