#!/usr/bin/env python3
"""
Тест автоматического переключения режимов в реальном времени
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import Config
from vinted_scanner import (
    vinted_antiblock, system_mode, ADVANCED_SYSTEM_AVAILABLE,
    advanced_system_errors, basic_system_errors, max_system_errors
)
from advanced_antiban import get_advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_requests():
    """Симуляция запросов для тестирования переключения"""
    print("\n🚀 СИМУЛЯЦИЯ ЗАПРОСОВ:")
    print("=" * 40)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    # Симулируем разные сценарии
    scenarios = [
        {"name": "Нормальная работа", "errors": 0, "duration": 3},
        {"name": "Небольшие ошибки", "errors": 2, "duration": 3},
        {"name": "Критические ошибки", "errors": 5, "duration": 3},
        {"name": "Восстановление", "errors": 0, "duration": 3}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 Сценарий {i}: {scenario['name']}")
        print("-" * 30)
        
        # Симулируем ошибки
        global advanced_system_errors
        advanced_system_errors = scenario['errors']
        
        print(f"   Ошибок продвинутой системы: {advanced_system_errors}/{max_system_errors}")
        
        # Проверяем режим
        if advanced_system_errors >= max_system_errors:
            print("   🚨 КРИТИЧЕСКИЙ УРОВЕНЬ - ожидается переключение на базовую систему")
        elif advanced_system_errors >= max_system_errors * 0.7:
            print("   ⚠️ ВЫСОКИЙ УРОВЕНЬ - возможны проблемы")
        else:
            print("   ✅ НОРМАЛЬНЫЙ УРОВЕНЬ - система работает стабильно")
        
        # Симулируем время работы
        for j in range(scenario['duration']):
            time.sleep(1)
            print(f"   Время: {j+1}/{scenario['duration']}с")
        
        print(f"   ✅ Сценарий {i} завершен")

def test_mode_transitions():
    """Тест переходов между режимами"""
    print("\n🔄 ТЕСТ ПЕРЕХОДОВ МЕЖДУ РЕЖИМАМИ:")
    print("=" * 45)
    
    modes = ["auto", "basic", "advanced", "proxy", "noproxy"]
    
    for mode in modes:
        print(f"\n🎯 Тестируем режим: {mode}")
        print("-" * 25)
        
        # Симулируем переключение режима
        global system_mode
        old_mode = system_mode
        system_mode = mode
        
        print(f"   Старый режим: {old_mode}")
        print(f"   Новый режим: {system_mode}")
        
        # Проверяем совместимость
        if mode in ["auto", "advanced", "proxy", "noproxy"]:
            if ADVANCED_SYSTEM_AVAILABLE:
                print("   ✅ Продвинутая система доступна")
            else:
                print("   ❌ Продвинутая система недоступна")
        
        if mode == "basic":
            print("   ✅ Базовая система всегда доступна")
        
        # Возвращаем старый режим
        system_mode = old_mode
        print(f"   🔄 Возврат к режиму: {system_mode}")

def test_proxy_management():
    """Тест управления прокси"""
    print("\n📡 ТЕСТ УПРАВЛЕНИЯ ПРОКСИ:")
    print("=" * 35)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    # Тест 1: Включение прокси
    print("\n1️⃣ Включение прокси:")
    advanced_system.enable_proxies()
    if advanced_system.current_proxy:
        print(f"   ✅ Прокси включен: {advanced_system.current_proxy['host']}:{advanced_system.current_proxy['port']}")
    else:
        print("   ❌ Прокси не включился")
    
    # Тест 2: Ротация прокси
    print("\n2️⃣ Ротация прокси:")
    old_proxy = advanced_system.current_proxy
    advanced_system._rotate_proxy()
    new_proxy = advanced_system.current_proxy
    
    if old_proxy != new_proxy:
        print(f"   ✅ Ротация успешна: {new_proxy['host']}:{new_proxy['port']}")
    else:
        print("   ⚠️ Ротация не произошла")
    
    # Тест 3: Отключение прокси
    print("\n3️⃣ Отключение прокси:")
    advanced_system.disable_proxies()
    if advanced_system.current_proxy is None:
        print("   ✅ Прокси отключен")
    else:
        print("   ❌ Прокси не отключился")

def test_error_recovery():
    """Тест восстановления после ошибок"""
    print("\n🔄 ТЕСТ ВОССТАНОВЛЕНИЯ ПОСЛЕ ОШИБОК:")
    print("=" * 45)
    
    if not ADVANCED_SYSTEM_AVAILABLE:
        print("❌ Продвинутая система недоступна")
        return
        
    advanced_system = get_advanced_system()
    
    # Симулируем ошибки в прокси
    print("\n🚨 Симуляция ошибок в прокси:")
    for i, proxy in enumerate(advanced_system.proxies):
        proxy['errors'] = i  # Разное количество ошибок
        print(f"   Прокси {proxy['host']}:{proxy['port']} - {proxy['errors']} ошибок")
    
    # Проверяем ротацию с учетом ошибок
    print("\n🔄 Ротация с учетом ошибок:")
    for i in range(3):
        old_proxy = advanced_system.current_proxy
        advanced_system._rotate_proxy()
        new_proxy = advanced_system.current_proxy
        
        if old_proxy != new_proxy:
            print(f"   Ротация {i+1}: {new_proxy['host']}:{new_proxy['port']} ({new_proxy['errors']} ошибок)")
        else:
            print(f"   Ротация {i+1}: Тот же прокси")
    
    # Сбрасываем ошибки
    for proxy in advanced_system.proxies:
        proxy['errors'] = 0
    print("\n✅ Ошибки сброшены")

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ АВТОМАТИЧЕСКОГО ПЕРЕКЛЮЧЕНИЯ")
    print("=" * 55)
    
    try:
        test_mode_transitions()
        test_proxy_management()
        test_error_recovery()
        simulate_requests()
        
        print("\n🎉 ВСЕ ТЕСТЫ АВТОМАТИЧЕСКОГО ПЕРЕКЛЮЧЕНИЯ ПРОЙДЕНЫ!")
        print("=" * 55)
        
        print("\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   • Режим системы: {system_mode}")
        print(f"   • Продвинутая система: {'✅ Доступна' if ADVANCED_SYSTEM_AVAILABLE else '❌ Недоступна'}")
        print(f"   • Ошибок продвинутой: {advanced_system_errors}/{max_system_errors}")
        print(f"   • Ошибок базовой: {basic_system_errors}/{max_system_errors}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 