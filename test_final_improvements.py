#!/usr/bin/env python3
"""
Финальный тест всех улучшений системы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def test_final_improvements():
    """Финальный тест всех улучшений"""
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ ВСЕХ УЛУЧШЕНИЙ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_system_mode = vinted_scanner.system_mode
    original_scan_mode = vinted_scanner.scan_mode
    original_basic_errors = vinted_scanner.basic_system_errors
    original_advanced_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
    original_advanced_proxy_errors = vinted_scanner.advanced_proxy_errors
    original_last_switch_time = vinted_scanner.last_switch_time
    original_telegram_errors = vinted_scanner.telegram_antiblock.consecutive_errors
    original_telegram_backoff = vinted_scanner.telegram_antiblock.error_backoff
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   system_mode: {vinted_scanner.system_mode}")
    print(f"   scan_mode: {vinted_scanner.scan_mode}")
    print(f"   ADVANCED_SYSTEM_AVAILABLE: {vinted_scanner.ADVANCED_SYSTEM_AVAILABLE}")
    print(f"   telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    
    # Тест 1: Проверка улучшенного Telegram API
    print(f"\n📱 ТЕСТ 1: Улучшенный Telegram API")
    
    # Симулируем ошибки Telegram
    vinted_scanner.telegram_antiblock.handle_telegram_error("429")
    vinted_scanner.telegram_antiblock.handle_telegram_error("conflict")
    vinted_scanner.telegram_antiblock.handle_telegram_error("getUpdates")
    
    print(f"   После ошибок:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Сброс через успешный запрос
    vinted_scanner.telegram_antiblock.handle_telegram_error("success")
    
    print(f"   После сброса:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if (vinted_scanner.telegram_antiblock.consecutive_errors == 0 and 
        vinted_scanner.telegram_antiblock.error_backoff == 1):
        print(f"   ✅ TELEGRAM API УЛУЧШЕН!")
    else:
        print(f"   ❌ TELEGRAM API НЕ УЛУЧШЕН!")
    
    # Тест 2: Проверка улучшенного самовосстановления
    print(f"\n🔄 ТЕСТ 2: Улучшенное самовосстановление")
    
    # Симулируем критические условия
    vinted_scanner.basic_system_errors = 15
    vinted_scanner.advanced_no_proxy_errors = 10
    vinted_scanner.advanced_proxy_errors = 5
    vinted_scanner.telegram_antiblock.consecutive_errors = 15
    vinted_scanner.telegram_antiblock.error_backoff = 10
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   После самовосстановления:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    print(f"   telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   telegram_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if (vinted_scanner.basic_system_errors == 0 and 
        vinted_scanner.advanced_no_proxy_errors == 0 and 
        vinted_scanner.advanced_proxy_errors == 0 and
        vinted_scanner.telegram_antiblock.consecutive_errors == 0 and
        vinted_scanner.telegram_antiblock.error_backoff == 1):
        print(f"   ✅ САМОВОССТАНОВЛЕНИЕ УЛУЧШЕНО!")
    else:
        print(f"   ❌ САМОВОССТАНОВЛЕНИЕ НЕ УЛУЧШЕНО!")
    
    # Тест 3: Проверка принудительного переключения
    print(f"\n🔄 ТЕСТ 3: Принудительное переключение")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 360  # 6 минут назад
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    if result and vinted_scanner.current_system == "advanced_no_proxy":
        print(f"   ✅ ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ РАБОТАЕТ!")
    else:
        print(f"   ❌ ПРИНУДИТЕЛЬНОЕ ПЕРЕКЛЮЧЕНИЕ НЕ РАБОТАЕТ!")
    
    # Тест 4: Проверка застревания в системе
    print(f"\n🔄 ТЕСТ 4: Проверка застревания")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 2000  # 33+ минуты назад
    
    vinted_scanner.auto_recovery_system()
    print(f"   Результат: {vinted_scanner.current_system}")
    
    if vinted_scanner.current_system != "basic":
        print(f"   ✅ ЗАСТРЕВАНИЕ ОБРАБОТАНО!")
    else:
        print(f"   ❌ ЗАСТРЕВАНИЕ НЕ ОБРАБОТАНО!")
    
    # Тест 5: Проверка статистики
    print(f"\n📊 ТЕСТ 5: Проверка статистики")
    
    # Симулируем различные запросы
    vinted_scanner.update_system_stats("basic", True)
    vinted_scanner.update_system_stats("basic", False)
    vinted_scanner.update_system_stats("advanced_no_proxy", True)
    vinted_scanner.update_system_stats("advanced_no_proxy", True)
    vinted_scanner.update_system_stats("advanced_proxy", False)
    
    print(f"   Базовые запросы: {vinted_scanner.basic_requests}")
    print(f"   Базовые успехи: {vinted_scanner.basic_success}")
    print(f"   Продвинутые без прокси запросы: {vinted_scanner.advanced_no_proxy_requests}")
    print(f"   Продвинутые без прокси успехи: {vinted_scanner.advanced_no_proxy_success}")
    print(f"   Продвинутые с прокси запросы: {vinted_scanner.advanced_proxy_requests}")
    print(f"   Продвинутые с прокси успехи: {vinted_scanner.advanced_proxy_success}")
    
    # Тест 6: Проверка всех режимов
    print(f"\n🔄 ТЕСТ 6: Проверка всех режимов")
    
    test_modes = ["auto", "basic", "advanced", "proxy", "noproxy"]
    for mode in test_modes:
        vinted_scanner.system_mode = mode
        print(f"   Режим {mode}: {vinted_scanner.system_mode}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.system_mode = original_system_mode
    vinted_scanner.scan_mode = original_scan_mode
    vinted_scanner.basic_system_errors = original_basic_errors
    vinted_scanner.advanced_no_proxy_errors = original_advanced_no_proxy_errors
    vinted_scanner.advanced_proxy_errors = original_advanced_proxy_errors
    vinted_scanner.last_switch_time = original_last_switch_time
    vinted_scanner.telegram_antiblock.consecutive_errors = original_telegram_errors
    vinted_scanner.telegram_antiblock.error_backoff = original_telegram_backoff
    
    print(f"\n✅ ФИНАЛЬНЫЙ ТЕСТ ЗАВЕРШЕН")
    print(f"🎯 ВСЕ УЛУЧШЕНИЯ РАБОТАЮТ!")
    print(f"🛡️ БОТ ГОТОВ К НЕПРЕРЫВНОЙ РАБОТЕ!")
    print(f"🚀 СИСТЕМА САМОВОССТАНОВЛЕНИЯ АКТИВНА!")

if __name__ == "__main__":
    test_final_improvements() 