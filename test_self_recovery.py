#!/usr/bin/env python3
"""
Тест системы самовосстановления
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def test_self_recovery():
    """Тестируем систему самовосстановления"""
    print("🔄 ТЕСТ СИСТЕМЫ САМОВОССТАНОВЛЕНИЯ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_basic_errors = vinted_scanner.basic_system_errors
    original_advanced_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
    original_advanced_proxy_errors = vinted_scanner.advanced_proxy_errors
    original_last_switch_time = vinted_scanner.last_switch_time
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    
    # Тест 1: Критический уровень ошибок
    print(f"\n🔄 ТЕСТ 1: Критический уровень ошибок (>20)")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 15
    vinted_scanner.advanced_no_proxy_errors = 10
    vinted_scanner.advanced_proxy_errors = 5
    vinted_scanner.last_switch_time = time.time()
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   Результат после самовосстановления:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    
    if (vinted_scanner.basic_system_errors == 0 and 
        vinted_scanner.advanced_no_proxy_errors == 0 and 
        vinted_scanner.advanced_proxy_errors == 0):
        print(f"   ✅ КРИТИЧЕСКИЕ ОШИБКИ СБРОШЕНЫ!")
    else:
        print(f"   ❌ КРИТИЧЕСКИЕ ОШИБКИ НЕ СБРОШЕНЫ!")
    
    # Тест 2: Застревание в системе
    print(f"\n🔄 ТЕСТ 2: Застревание в системе (>30 минут)")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 2000  # 33+ минуты назад
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   Результат после самовосстановления:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
    
    if vinted_scanner.current_system != "basic":
        print(f"   ✅ СИСТЕМА ПЕРЕКЛЮЧЕНА ПРИ ЗАСТРЕВАНИИ!")
    else:
        print(f"   ❌ СИСТЕМА НЕ ПЕРЕКЛЮЧЕНА ПРИ ЗАСТРЕВАНИИ!")
    
    # Тест 3: Telegram ошибки
    print(f"\n🔄 ТЕСТ 3: Telegram ошибки")
    
    vinted_scanner.telegram_antiblock.consecutive_errors = 15
    vinted_scanner.telegram_antiblock.error_backoff = 5
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   Результат после самовосстановления:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if (vinted_scanner.telegram_antiblock.consecutive_errors == 0 and 
        vinted_scanner.telegram_antiblock.error_backoff == 1):
        print(f"   ✅ TELEGRAM ОШИБКИ СБРОШЕНЫ!")
    else:
        print(f"   ❌ TELEGRAM ОШИБКИ НЕ СБРОШЕНЫ!")
    
    # Тест 4: Проверка логики переключения систем
    print(f"\n🔄 ТЕСТ 4: Логика переключения систем")
    
    # Тест переключения с basic на advanced_no_proxy
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 2000
    vinted_scanner.auto_recovery_system()
    
    print(f"   basic -> advanced_no_proxy: {vinted_scanner.current_system}")
    
    # Тест переключения с advanced_no_proxy на advanced_proxy
    vinted_scanner.current_system = "advanced_no_proxy"
    vinted_scanner.last_switch_time = time.time() - 2000
    vinted_scanner.auto_recovery_system()
    
    print(f"   advanced_no_proxy -> advanced_proxy: {vinted_scanner.current_system}")
    
    # Тест переключения с advanced_proxy обратно на advanced_no_proxy
    vinted_scanner.current_system = "advanced_proxy"
    vinted_scanner.last_switch_time = time.time() - 2000
    vinted_scanner.auto_recovery_system()
    
    print(f"   advanced_proxy -> advanced_no_proxy: {vinted_scanner.current_system}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.basic_system_errors = original_basic_errors
    vinted_scanner.advanced_no_proxy_errors = original_advanced_no_proxy_errors
    vinted_scanner.advanced_proxy_errors = original_advanced_proxy_errors
    vinted_scanner.last_switch_time = original_last_switch_time
    
    print(f"\n✅ ТЕСТ САМОВОССТАНОВЛЕНИЯ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_self_recovery() 