#!/usr/bin/env python3
"""
Полный тест всей логики системы
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_complete_logic():
    """Полный тест всей логики системы"""
    
    print("🧪 ПОЛНЫЙ ТЕСТ ЛОГИКИ СИСТЕМЫ")
    print("=" * 60)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    print("\n📊 ТЕСТ 1: Начальное состояние (без прокси)")
    print("-" * 40)
    
    # Симулируем начальное состояние
    system.proxy_mode = "auto"
    system.http_requests = 0
    system.http_success = 0
    system.errors_403 = 0
    system.errors_429 = 0
    system.errors_521 = 0
    system.consecutive_errors = 0
    
    print(f"🔧 Режим: {system.proxy_mode}")
    print(f"📊 Запросы: {system.http_requests}")
    print(f"📊 Успешность: {system.http_success}")
    
    # Тестируем _should_use_proxy
    should_use = system._should_use_proxy()
    print(f"🔍 Должен ли использовать прокси: {should_use}")
    
    print("\n📊 ТЕСТ 2: Хорошая работа без прокси")
    print("-" * 40)
    
    # Симулируем хорошую работу без прокси
    system.http_requests = 20
    system.http_success = 18  # 90% успешность
    system.errors_403 = 1
    system.consecutive_errors = 0
    
    print(f"📊 Статистика: успешность={system.http_success/system.http_requests*100:.1f}%, ошибок=1")
    
    should_use = system._should_use_proxy()
    print(f"🔍 Должен ли использовать прокси: {should_use}")
    
    print("\n📊 ТЕСТ 3: Проблемы - включаем прокси")
    print("-" * 40)
    
    # Симулируем проблемы
    system.http_requests = 10
    system.http_success = 5  # 50% успешность
    system.errors_403 = 3
    system.errors_429 = 1
    system.consecutive_errors = 3
    
    print(f"📊 Статистика: успешность={system.http_success/system.http_requests*100:.1f}%, ошибок=4, подряд=3")
    
    should_use = system._should_use_proxy()
    print(f"🔍 Должен ли использовать прокси: {should_use}")
    
    print("\n📊 ТЕСТ 4: Проверка работы без прокси")
    print("-" * 40)
    
    # Симулируем хорошую работу с прокси
    system.proxy_mode = "enabled"
    system.http_requests = 30
    system.http_success = 27  # 90% успешность
    system.errors_403 = 2
    system.consecutive_errors = 0
    system.no_proxy_test_attempts = 0
    
    print(f"📊 Статистика с прокси: успешность={system.http_success/system.http_requests*100:.1f}%, ошибок=2")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    print(f"📈 Попытки проверки без прокси: {system.no_proxy_test_attempts}")
    
    # Симулируем время для проверки
    system.last_proxy_switch_time = time.time() - 700
    
    # Вызываем проверку
    system._check_no_proxy_workability()
    
    print(f"📊 После проверки:")
    print(f"🔧 Режим прокси: {system.proxy_mode}")
    print(f"📈 Попытки проверки без прокси: {system.no_proxy_test_attempts}")
    
    print("\n📊 ТЕСТ 5: Статистика системы")
    print("-" * 40)
    
    # Получаем статистику
    stats = system.get_stats()
    
    print("📊 Полная статистика:")
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"   {key}: {value}")
    
    print("\n✅ Все тесты завершены!")

if __name__ == "__main__":
    test_complete_logic() 