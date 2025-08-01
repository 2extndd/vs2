#!/usr/bin/env python3
"""
Тест принудительного переключения на продвинутую систему
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def test_force_advanced():
    """Тестируем принудительное переключение на продвинутую систему"""
    print("🚀 ТЕСТ ПРИНУДИТЕЛЬНОГО ПЕРЕКЛЮЧЕНИЯ НА ПРОДВИНУТУЮ СИСТЕМУ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_last_switch_time = vinted_scanner.last_switch_time
    original_basic_errors = vinted_scanner.basic_system_errors
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
    
    # Тест 1: Принудительное переключение по времени
    print(f"\n🔄 ТЕСТ 1: Принудительное переключение по времени (5 минут)")
    
    # Устанавливаем время последнего переключения 6 минут назад
    vinted_scanner.last_switch_time = time.time() - 360  # 6 минут назад
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 0
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    if result and vinted_scanner.current_system == "advanced_no_proxy":
        print(f"   ✅ ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ ПО ВРЕМЕНИ РАБОТАЕТ!")
    else:
        print(f"   ❌ ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ ПО ВРЕМЕНИ НЕ РАБОТАЕТ!")
    
    # Тест 2: Принудительное переключение по ошибкам
    print(f"\n🔄 ТЕСТ 2: Принудительное переключение по ошибкам")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 3  # Достигаем лимита
    vinted_scanner.last_switch_time = time.time()  # Сбрасываем время
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    if result and vinted_scanner.current_system == "advanced_no_proxy":
        print(f"   ✅ ПЕРЕКЛЮЧЕНИЕ ПО ОШИБКАМ РАБОТАЕТ!")
    else:
        print(f"   ❌ ПЕРЕКЛЮЧЕНИЕ ПО ОШИБКАМ НЕ РАБОТАЕТ!")
    
    # Тест 3: Переключение с продвинутой без прокси на продвинутую с прокси
    print(f"\n🔄 ТЕСТ 3: Переключение на прокси при ошибках")
    
    vinted_scanner.current_system = "advanced_no_proxy"
    vinted_scanner.advanced_no_proxy_errors = 3  # Достигаем лимита
    vinted_scanner.last_switch_time = time.time()
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    if result and vinted_scanner.current_system == "advanced_proxy":
        print(f"   ✅ ПЕРЕКЛЮЧЕНИЕ НА ПРОКСИ РАБОТАЕТ!")
    else:
        print(f"   ❌ ПЕРЕКЛЮЧЕНИЕ НА ПРОКСИ НЕ РАБОТАЕТ!")
    
    # Тест 4: Возврат с прокси на без прокси при ошибках прокси
    print(f"\n🔄 ТЕСТ 4: Возврат с прокси на без прокси при ошибках")
    
    vinted_scanner.current_system = "advanced_proxy"
    vinted_scanner.advanced_proxy_errors = 3  # Достигаем лимита
    vinted_scanner.last_switch_time = time.time()
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    if result and vinted_scanner.current_system == "advanced_no_proxy":
        print(f"   ✅ ВОЗВРАТ С ПРОКСИ РАБОТАЕТ!")
    else:
        print(f"   ❌ ВОЗВРАТ С ПРОКСИ НЕ РАБОТАЕТ!")
    
    # Тест 5: Проверка статистики
    print(f"\n📊 ТЕСТ 5: Проверка статистики систем")
    
    # Симулируем успешные запросы
    vinted_scanner.update_system_stats("basic", True)
    vinted_scanner.update_system_stats("basic", True)
    vinted_scanner.update_system_stats("advanced_no_proxy", True)
    vinted_scanner.update_system_stats("advanced_no_proxy", False)
    
    print(f"   Базовые запросы: {vinted_scanner.basic_requests}")
    print(f"   Базовые успехи: {vinted_scanner.basic_success}")
    print(f"   Продвинутые без прокси запросы: {vinted_scanner.advanced_no_proxy_requests}")
    print(f"   Продвинутые без прокси успехи: {vinted_scanner.advanced_no_proxy_success}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.last_switch_time = original_last_switch_time
    vinted_scanner.basic_system_errors = original_basic_errors
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_force_advanced() 