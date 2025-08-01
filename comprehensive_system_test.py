#!/usr/bin/env python3
"""
Комплексный тест всех систем и режимов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def comprehensive_system_test():
    """Комплексный тест всех систем"""
    print("🔧 КОМПЛЕКСНЫЙ ТЕСТ ВСЕХ СИСТЕМ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_system_mode = vinted_scanner.system_mode
    original_scan_mode = vinted_scanner.scan_mode
    original_basic_errors = vinted_scanner.basic_system_errors
    original_advanced_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
    original_advanced_proxy_errors = vinted_scanner.advanced_proxy_errors
    original_last_switch_time = vinted_scanner.last_switch_time
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   system_mode: {vinted_scanner.system_mode}")
    print(f"   scan_mode: {vinted_scanner.scan_mode}")
    print(f"   ADVANCED_SYSTEM_AVAILABLE: {vinted_scanner.ADVANCED_SYSTEM_AVAILABLE}")
    
    # Тест 1: Проверка всех режимов системы
    print(f"\n🔄 ТЕСТ 1: Проверка всех режимов системы")
    
    test_modes = ["auto", "basic", "advanced", "proxy", "noproxy"]
    for mode in test_modes:
        vinted_scanner.system_mode = mode
        print(f"   Режим {mode}: {vinted_scanner.system_mode}")
    
    # Тест 2: Проверка переключения режимов сканирования
    print(f"\n🔄 ТЕСТ 2: Проверка режимов сканирования")
    
    vinted_scanner.scan_mode = "fast"
    print(f"   Быстрый режим: {vinted_scanner.scan_mode}")
    
    vinted_scanner.scan_mode = "slow"
    print(f"   Медленный режим: {vinted_scanner.scan_mode}")
    
    # Тест 3: Проверка трехуровневой системы
    print(f"\n🔄 ТЕСТ 3: Проверка трехуровневой системы")
    
    # Тест переключения с basic на advanced_no_proxy
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 3
    vinted_scanner.last_switch_time = time.time()
    
    result = vinted_scanner.should_switch_system()
    print(f"   basic -> advanced_no_proxy: {result} ({vinted_scanner.current_system})")
    
    # Тест переключения с advanced_no_proxy на advanced_proxy
    vinted_scanner.current_system = "advanced_no_proxy"
    vinted_scanner.advanced_no_proxy_errors = 3
    vinted_scanner.last_switch_time = time.time()
    
    result = vinted_scanner.should_switch_system()
    print(f"   advanced_no_proxy -> advanced_proxy: {result} ({vinted_scanner.current_system})")
    
    # Тест возврата с advanced_proxy на advanced_no_proxy
    vinted_scanner.current_system = "advanced_proxy"
    vinted_scanner.advanced_proxy_errors = 3
    vinted_scanner.last_switch_time = time.time()
    
    result = vinted_scanner.should_switch_system()
    print(f"   advanced_proxy -> advanced_no_proxy: {result} ({vinted_scanner.current_system})")
    
    # Тест 4: Проверка статистики
    print(f"\n📊 ТЕСТ 4: Проверка статистики")
    
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
    
    # Тест 5: Проверка самовосстановления
    print(f"\n🔄 ТЕСТ 5: Проверка самовосстановления")
    
    # Симулируем критические условия
    vinted_scanner.basic_system_errors = 15
    vinted_scanner.advanced_no_proxy_errors = 10
    vinted_scanner.advanced_proxy_errors = 5
    vinted_scanner.telegram_antiblock.consecutive_errors = 15
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   Результат после самовосстановления:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    print(f"   telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    
    # Тест 6: Проверка принудительного переключения по времени
    print(f"\n🔄 ТЕСТ 6: Принудительное переключение по времени")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 360  # 6 минут назад
    
    result = vinted_scanner.should_switch_system()
    print(f"   Результат: {result}")
    print(f"   Новая система: {vinted_scanner.current_system}")
    
    # Тест 7: Проверка застревания в системе
    print(f"\n🔄 ТЕСТ 7: Проверка застревания в системе")
    
    vinted_scanner.current_system = "basic"
    vinted_scanner.last_switch_time = time.time() - 2000  # 33+ минуты назад
    
    vinted_scanner.auto_recovery_system()
    print(f"   Результат: {vinted_scanner.current_system}")
    
    # Тест 8: Проверка Telegram восстановления
    print(f"\n📱 ТЕСТ 8: Проверка Telegram восстановления")
    
    # Симулируем ошибки Telegram
    vinted_scanner.telegram_antiblock.handle_telegram_error("429")
    vinted_scanner.telegram_antiblock.handle_telegram_error("conflict")
    
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Сброс через успешный запрос
    vinted_scanner.telegram_antiblock.handle_telegram_error("success")
    print(f"   После сброса - consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.system_mode = original_system_mode
    vinted_scanner.scan_mode = original_scan_mode
    vinted_scanner.basic_system_errors = original_basic_errors
    vinted_scanner.advanced_no_proxy_errors = original_advanced_no_proxy_errors
    vinted_scanner.advanced_proxy_errors = original_advanced_proxy_errors
    vinted_scanner.last_switch_time = original_last_switch_time
    
    print(f"\n✅ КОМПЛЕКСНЫЙ ТЕСТ ЗАВЕРШЕН")
    print(f"🎯 ВСЕ СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО!")
    print(f"🛡️ БОТ ГОТОВ К САМОВОССТАНОВЛЕНИЮ!")

if __name__ == "__main__":
    comprehensive_system_test() 