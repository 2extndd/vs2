#!/usr/bin/env python3
"""
Простой тест переключения обратно на режим без прокси
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_simple_switch():
    """Простой тест переключения обратно на режим без прокси"""
    
    print("🧪 ПРОСТОЙ ТЕСТ ПЕРЕКЛЮЧЕНИЯ")
    print("=" * 60)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    print(f"📊 1. НАЧАЛЬНОЕ СОСТОЯНИЕ:")
    print(f"   proxy_mode: {system.proxy_mode}")
    print(f"   current_proxy: {system.current_proxy}")
    
    # Устанавливаем режим enabled и прокси
    system.proxy_mode = "enabled"
    system._rotate_proxy()
    print(f"\n📊 2. УСТАНОВИЛИ РЕЖИМ ENABLED:")
    print(f"   proxy_mode: {system.proxy_mode}")
    print(f"   current_proxy: {system.current_proxy}")
    
    # Устанавливаем хорошую статистику
    system.http_requests = 10
    system.http_success = 9
    system.errors_403 = 0
    system.errors_429 = 0
    system.errors_521 = 0
    system.consecutive_errors = 0
    
    # Сбрасываем время последней проверки
    import time
    system.last_proxy_switch_time = time.time() - 120  # 2 минуты назад
    
    print(f"\n📊 3. УСТАНОВИЛИ ХОРОШУЮ СТАТИСТИКУ:")
    print(f"   http_requests: {system.http_requests}")
    print(f"   http_success: {system.http_success}")
    print(f"   errors: {system.errors_403 + system.errors_429 + system.errors_521}")
    print(f"   consecutive_errors: {system.consecutive_errors}")
    print(f"   success_rate: {(system.http_success / system.http_requests * 100):.1f}%")
    
    # Проверяем условия
    total_errors = system.errors_403 + system.errors_429 + system.errors_521
    success_rate = (system.http_success / system.http_requests * 100) if system.http_requests > 0 else 0
    
    print(f"\n📊 4. ПРОВЕРЯЕМ УСЛОВИЯ:")
    print(f"   success_rate > 70: {success_rate > 70} ({success_rate:.1f}%)")
    print(f"   total_errors < 3: {total_errors < 3} ({total_errors})")
    print(f"   consecutive_errors < 2: {system.consecutive_errors < 2} ({system.consecutive_errors})")
    
    conditions_met = (success_rate > 70 and total_errors < 3 and system.consecutive_errors < 2)
    print(f"   Все условия выполнены: {conditions_met}")
    
    # Вызываем проверку
    print(f"\n📊 5. ВЫЗЫВАЕМ ПРОВЕРКУ:")
    original_mode = system.proxy_mode
    original_proxy = system.current_proxy
    
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
        print(f"   Причина: условия не выполнены или логика не работает")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_simple_switch() 