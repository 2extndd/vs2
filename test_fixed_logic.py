#!/usr/bin/env python3
"""
Тест исправленной логики переключения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def test_fixed_logic():
    """Тестируем исправленную логику"""
    print("🔧 ТЕСТ ИСПРАВЛЕННОЙ ЛОГИКИ")
    print("=" * 40)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_basic_errors = vinted_scanner.basic_system_errors
    original_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
    original_proxy_errors = vinted_scanner.advanced_proxy_errors
    
    print(f"📊 ТЕСТ 1: Переключение advanced_proxy -> advanced_no_proxy при ошибках прокси")
    
    # Устанавливаем условия для теста
    vinted_scanner.current_system = "advanced_proxy"
    vinted_scanner.advanced_proxy_errors = 3  # Достигаем лимита ошибок
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.basic_system_errors = 0
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    print(f"   advanced_proxy_errors после сброса: {vinted_scanner.advanced_proxy_errors}")
    
    if result and vinted_scanner.current_system == "advanced_no_proxy":
        print(f"   ✅ ИСПРАВЛЕНИЕ РАБОТАЕТ!")
    else:
        print(f"   ❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ!")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.basic_system_errors = original_basic_errors
    vinted_scanner.advanced_no_proxy_errors = original_no_proxy_errors
    vinted_scanner.advanced_proxy_errors = original_proxy_errors
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_fixed_logic() 