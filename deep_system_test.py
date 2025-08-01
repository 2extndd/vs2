#!/usr/bin/env python3
"""
Глубокий тест системы для анализа проблемы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time
import logging

def deep_system_test():
    """Глубокий тест системы"""
    print("🔍 ГЛУБОКИЙ ТЕСТ СИСТЕМЫ")
    print("=" * 50)
    
    # 1. Проверяем глобальные переменные
    print(f"\n📊 ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    print(f"   max_errors_before_switch: {vinted_scanner.max_errors_before_switch}")
    print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
    print(f"   switch_interval: {vinted_scanner.switch_interval}")
    
    # 2. Проверяем статистику
    print(f"\n📈 СТАТИСТИКА:")
    print(f"   basic_requests: {vinted_scanner.basic_requests}")
    print(f"   basic_success: {vinted_scanner.basic_success}")
    print(f"   advanced_no_proxy_requests: {vinted_scanner.advanced_no_proxy_requests}")
    print(f"   advanced_no_proxy_success: {vinted_scanner.advanced_no_proxy_success}")
    print(f"   advanced_proxy_requests: {vinted_scanner.advanced_proxy_requests}")
    print(f"   advanced_proxy_success: {vinted_scanner.advanced_proxy_success}")
    
    # 3. Проверяем продвинутую систему
    print(f"\n🚀 ПРОДВИНУТАЯ СИСТЕМА:")
    print(f"   ADVANCED_SYSTEM_AVAILABLE: {vinted_scanner.ADVANCED_SYSTEM_AVAILABLE}")
    if vinted_scanner.ADVANCED_SYSTEM_AVAILABLE:
        print(f"   advanced_system ID: {id(vinted_scanner.advanced_system)}")
        print(f"   proxy_mode: {vinted_scanner.advanced_system.proxy_mode}")
        print(f"   current_proxy: {vinted_scanner.advanced_system.current_proxy}")
        print(f"   proxies count: {len(vinted_scanner.advanced_system.proxies)}")
    
    # 4. Тестируем логику переключения
    print(f"\n🔄 ТЕСТ ЛОГИКИ ПЕРЕКЛЮЧЕНИЯ:")
    
    # Сохраняем текущие значения
    original_system = vinted_scanner.current_system
    original_basic_errors = vinted_scanner.basic_system_errors
    original_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
    original_proxy_errors = vinted_scanner.advanced_proxy_errors
    
    # Тест 1: Переключение с basic на advanced_no_proxy
    print(f"   Тест 1: Переключение basic -> advanced_no_proxy")
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 3  # Достигаем лимита
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.advanced_proxy_errors = 0
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    # Тест 2: Переключение с advanced_no_proxy на advanced_proxy
    print(f"   Тест 2: Переключение advanced_no_proxy -> advanced_proxy")
    vinted_scanner.current_system = "advanced_no_proxy"
    vinted_scanner.basic_system_errors = 0
    vinted_scanner.advanced_no_proxy_errors = 3  # Достигаем лимита
    vinted_scanner.advanced_proxy_errors = 0
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    # Тест 3: Переключение обратно с advanced_proxy на advanced_no_proxy
    print(f"   Тест 3: Переключение advanced_proxy -> advanced_no_proxy")
    vinted_scanner.current_system = "advanced_proxy"
    vinted_scanner.basic_system_errors = 0
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.advanced_proxy_errors = 3  # Достигаем лимита
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.basic_system_errors = original_basic_errors
    vinted_scanner.advanced_no_proxy_errors = original_no_proxy_errors
    vinted_scanner.advanced_proxy_errors = original_proxy_errors
    
    # 5. Тестируем update_system_stats
    print(f"\n📊 ТЕСТ UPDATE_SYSTEM_STATS:")
    
    # Сохраняем оригинальные значения
    original_basic_requests = vinted_scanner.basic_requests
    original_basic_success = vinted_scanner.basic_success
    original_no_proxy_requests = vinted_scanner.advanced_no_proxy_requests
    original_no_proxy_success = vinted_scanner.advanced_no_proxy_success
    original_proxy_requests = vinted_scanner.advanced_proxy_requests
    original_proxy_success = vinted_scanner.advanced_proxy_success
    
    # Тест успешного запроса
    print(f"   Тест успешного запроса basic:")
    vinted_scanner.update_system_stats("basic", success=True)
    print(f"   basic_requests: {vinted_scanner.basic_requests}")
    print(f"   basic_success: {vinted_scanner.basic_success}")
    
    # Тест неудачного запроса
    print(f"   Тест неудачного запроса basic:")
    vinted_scanner.update_system_stats("basic", success=False)
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.basic_requests = original_basic_requests
    vinted_scanner.basic_success = original_basic_success
    vinted_scanner.advanced_no_proxy_requests = original_no_proxy_requests
    vinted_scanner.advanced_no_proxy_success = original_no_proxy_success
    vinted_scanner.advanced_proxy_requests = original_proxy_requests
    vinted_scanner.advanced_proxy_success = original_proxy_success
    
    # 6. Проверяем проблемные места
    print(f"\n⚠️ ПОТЕНЦИАЛЬНЫЕ ПРОБЛЕМЫ:")
    
    # Проблема 1: Счетчики ошибок не сбрасываются при успехе
    if vinted_scanner.basic_system_errors > 0:
        print(f"   ❌ basic_system_errors > 0: {vinted_scanner.basic_system_errors}")
        print(f"      Это может мешать переключению обратно на basic")
    
    if vinted_scanner.advanced_no_proxy_errors > 0:
        print(f"   ❌ advanced_no_proxy_errors > 0: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"      Это может мешать переключению обратно на advanced_no_proxy")
    
    if vinted_scanner.advanced_proxy_errors > 0:
        print(f"   ❌ advanced_proxy_errors > 0: {vinted_scanner.advanced_proxy_errors}")
        print(f"      Это может мешать переключению обратно на advanced_proxy")
    
    # Проблема 2: Проверяем логику переключения обратно
    print(f"\n🔄 ПРОВЕРКА ЛОГИКИ ПЕРЕКЛЮЧЕНИЯ ОБРАТНО:")
    
    # Должна быть логика переключения обратно при успехах
    if vinted_scanner.advanced_no_proxy_success >= 5 and vinted_scanner.advanced_no_proxy_errors == 0:
        print(f"   ✅ Можно переключиться обратно на advanced_no_proxy")
    
    if vinted_scanner.basic_success >= 5 and vinted_scanner.basic_system_errors == 0:
        print(f"   ✅ Можно переключиться обратно на basic")
    
    print(f"\n✅ ГЛУБОКИЙ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    deep_system_test() 