#!/usr/bin/env python3
"""
Тест автоматического переключения обратно на режим без прокси
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_auto_switch_back():
    """Тест автоматического переключения обратно на режим без прокси"""
    
    print("🧪 ТЕСТ АВТОМАТИЧЕСКОГО ПЕРЕКЛЮЧЕНИЯ ОБРАТНО")
    print("=" * 60)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    print(f"📊 1. НАЧАЛЬНОЕ СОСТОЯНИЕ:")
    print(f"   proxy_mode: {system.proxy_mode}")
    print(f"   current_proxy: {system.current_proxy}")
    
    # Симулируем проблемы для переключения на прокси
    print(f"\n📊 2. СИМУЛЯЦИЯ ПРОБЛЕМ (ПЕРЕКЛЮЧЕНИЕ НА ПРОКСИ):")
    for i in range(3):
        system.http_requests += 1
        system.errors_403 += 1
        system.consecutive_errors += 1
        system.no_proxy_requests += 1
        print(f"   Ошибка {i+1}: 403 Forbidden")
    
    # Активируем прокси
    if system._should_use_proxy():
        system.proxy_mode = "enabled"
        system._rotate_proxy()
        print(f"   ✅ Прокси активирован: {system.current_proxy}")
    
    # Симулируем стабильную работу с прокси
    print(f"\n📊 3. СИМУЛЯЦИЯ СТАБИЛЬНОЙ РАБОТЫ С ПРОКСИ:")
    for i in range(5):
        system.http_requests += 1
        system.http_success += 1
        system.proxy_requests += 1
        system.proxy_success += 1
        system.consecutive_errors = 0  # Сбрасываем ошибки
        print(f"   Успешный запрос {i+1} с прокси")
    
    print(f"   http_success: {system.http_success}")
    print(f"   consecutive_errors: {system.consecutive_errors}")
    print(f"   success_rate: {(system.http_success / system.http_requests * 100):.1f}%")
    
    # Проверяем условия для тестирования без прокси
    print(f"\n📊 4. ПРОВЕРКА УСЛОВИЙ ДЛЯ ТЕСТА БЕЗ ПРОКСИ:")
    total_errors = system.errors_403 + system.errors_429 + system.errors_521
    success_rate = (system.http_success / system.http_requests * 100) if system.http_requests > 0 else 0
    
    print(f"   success_rate: {success_rate:.1f}% (нужно > 80%)")
    print(f"   total_errors: {total_errors} (нужно < 2)")
    print(f"   consecutive_errors: {system.consecutive_errors} (нужно < 2)")
    
    if (success_rate > 80 and total_errors < 2 and system.consecutive_errors < 2):
        print(f"   ✅ Условия для теста без прокси выполнены")
    else:
        print(f"   ❌ Условия для теста без прокси НЕ выполнены")
        # Симулируем улучшение статистики
        print(f"   🔧 Симулируем улучшение статистики...")
        system.http_requests += 3
        system.http_success += 3
        system.proxy_requests += 3
        system.proxy_success += 3
        system.errors_403 = 0
        system.errors_429 = 0
        system.errors_521 = 0
        system.consecutive_errors = 0
        
        success_rate = (system.http_success / system.http_requests * 100)
        print(f"   📊 Новая статистика: успешность={success_rate:.1f}%, ошибок=0")
    
    # Симулируем вызов проверки без прокси
    print(f"\n📊 5. СИМУЛЯЦИЯ ПРОВЕРКИ БЕЗ ПРОКСИ:")
    print(f"   Вызываем _check_no_proxy_workability()...")
    
    # Сохраняем текущие значения для сравнения
    original_mode = system.proxy_mode
    original_proxy = system.current_proxy
    
    # Вызываем проверку
    system._check_no_proxy_workability()
    
    print(f"   Режим до: {original_mode}")
    print(f"   Режим после: {system.proxy_mode}")
    print(f"   Прокси до: {original_proxy}")
    print(f"   Прокси после: {system.current_proxy}")
    
    # Анализируем результат
    if system.proxy_mode == "disabled" and system.current_proxy is None:
        print(f"   ✅ УСПЕШНО: Система переключилась обратно на режим без прокси")
    else:
        print(f"   ❌ НЕУДАЧНО: Система осталась в режиме с прокси")
    
    # Получаем финальную статистику
    stats = system.get_stats()
    print(f"\n📊 6. ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"   no_proxy_requests: {stats.get('no_proxy_requests', 0)}")
    print(f"   no_proxy_success: {stats.get('no_proxy_success', 0)}")
    print(f"   proxy_requests: {stats.get('proxy_requests', 0)}")
    print(f"   proxy_success: {stats.get('proxy_success', 0)}")
    print(f"   proxy_mode: {system.proxy_mode}")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_auto_switch_back() 