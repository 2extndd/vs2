#!/usr/bin/env python3
"""
Тест проверки работы без прокси
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_no_proxy_check():
    """Тест проверки работы без прокси"""
    
    print("🧪 ТЕСТ ПРОВЕРКИ РАБОТЫ БЕЗ ПРОКСИ")
    print("=" * 50)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    # Симулируем хорошую статистику с прокси
    print("\n📊 ТЕСТ 1: Хорошая статистика с прокси")
    system.proxy_mode = "enabled"
    system.http_requests = 20
    system.http_success = 18  # 90% успешность
    system.errors_403 = 1
    system.errors_429 = 0
    system.errors_521 = 0
    system.consecutive_errors = 0
    system.no_proxy_test_attempts = 0
    
    print(f"📊 Статистика: успешность={system.http_success/system.http_requests*100:.1f}%, ошибок=1")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    print(f"📈 Попытки проверки без прокси: {system.no_proxy_test_attempts}")
    
    # Симулируем вызов проверки
    print("\n🔍 Симулируем проверку работы без прокси...")
    
    # Устанавливаем время для срабатывания проверки
    system.last_proxy_switch_time = time.time() - 700  # 11 минут назад
    
    # Вызываем проверку
    system._check_no_proxy_workability()
    
    print(f"📊 После проверки:")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    print(f"📈 Попытки проверки без прокси: {system.no_proxy_test_attempts}")
    
    # Тест 2: Плохая статистика
    print("\n📊 ТЕСТ 2: Плохая статистика")
    system.proxy_mode = "enabled"
    system.http_requests = 10
    system.http_success = 5  # 50% успешность
    system.errors_403 = 3
    system.consecutive_errors = 2
    
    print(f"📊 Статистика: успешность={system.http_success/system.http_requests*100:.1f}%, ошибок=3")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    
    # Сбрасываем время
    system.last_proxy_switch_time = time.time() - 700
    
    # Вызываем проверку
    system._check_no_proxy_workability()
    
    print(f"📊 После проверки:")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    print(f"📈 Попытки проверки без прокси: {system.no_proxy_test_attempts}")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_no_proxy_check() 