#!/usr/bin/env python3
"""
Тест восстановления Telegram API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time

def test_telegram_recovery():
    """Тестируем восстановление Telegram API"""
    print("📱 ТЕСТ ВОССТТАНОВЛЕНИЯ TELEGRAM API")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_consecutive_errors = vinted_scanner.telegram_antiblock.consecutive_errors
    original_error_backoff = vinted_scanner.telegram_antiblock.error_backoff
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Тест 1: Обработка ошибки 429
    print(f"\n🔄 ТЕСТ 1: Обработка ошибки 429")
    
    vinted_scanner.telegram_antiblock.consecutive_errors = 0
    vinted_scanner.telegram_antiblock.error_backoff = 1
    
    # Симулируем ошибку 429
    vinted_scanner.telegram_antiblock.handle_telegram_error("429")
    
    print(f"   Результат после обработки ошибки 429:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if vinted_scanner.telegram_antiblock.consecutive_errors == 1:
        print(f"   ✅ ОШИБКА 429 ОБРАБОТАНА!")
    else:
        print(f"   ❌ ОШИБКА 429 НЕ ОБРАБОТАНА!")
    
    # Тест 2: Обработка конфликта getUpdates
    print(f"\n🔄 ТЕСТ 2: Обработка конфликта getUpdates")
    
    vinted_scanner.telegram_antiblock.handle_telegram_error("conflict")
    
    print(f"   Результат после обработки конфликта:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if vinted_scanner.telegram_antiblock.consecutive_errors == 2:
        print(f"   ✅ КОНФЛИКТ ОБРАБОТАН!")
    else:
        print(f"   ❌ КОНФЛИКТ НЕ ОБРАБОТАН!")
    
    # Тест 3: Увеличение backoff при множественных ошибках
    print(f"\n🔄 ТЕСТ 3: Увеличение backoff при множественных ошибках")
    
    # Симулируем 5 ошибок подряд
    for i in range(5):
        vinted_scanner.telegram_antiblock.handle_telegram_error("429")
    
    print(f"   Результат после 5 ошибок:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if vinted_scanner.telegram_antiblock.error_backoff > 1:
        print(f"   ✅ BACKOFF УВЕЛИЧЕН!")
    else:
        print(f"   ❌ BACKOFF НЕ УВЕЛИЧЕН!")
    
    # Тест 4: Сброс при успешном запросе
    print(f"\n🔄 ТЕСТ 4: Сброс при успешном запросе")
    
    vinted_scanner.telegram_antiblock.handle_telegram_error("success")
    
    print(f"   Результат после успешного запроса:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if (vinted_scanner.telegram_antiblock.consecutive_errors == 0 and 
        vinted_scanner.telegram_antiblock.error_backoff == 1):
        print(f"   ✅ СЧЕТЧИКИ СБРОШЕНЫ ПРИ УСПЕХЕ!")
    else:
        print(f"   ❌ СЧЕТЧИКИ НЕ СБРОШЕНЫ ПРИ УСПЕХЕ!")
    
    # Тест 5: Автоматическое самовосстановление
    print(f"\n🔄 ТЕСТ 5: Автоматическое самовосстановление")
    
    # Симулируем критическое количество ошибок
    vinted_scanner.telegram_antiblock.consecutive_errors = 15
    vinted_scanner.telegram_antiblock.error_backoff = 10
    
    vinted_scanner.auto_recovery_system()
    
    print(f"   Результат после самовосстановления:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    if (vinted_scanner.telegram_antiblock.consecutive_errors == 0 and 
        vinted_scanner.telegram_antiblock.error_backoff == 1):
        print(f"   ✅ АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ РАБОТАЕТ!")
    else:
        print(f"   ❌ АВТОМАТИЧЕСКОЕ САМОВОССТАНОВЛЕНИЕ НЕ РАБОТАЕТ!")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.telegram_antiblock.consecutive_errors = original_consecutive_errors
    vinted_scanner.telegram_antiblock.error_backoff = original_error_backoff
    
    print(f"\n✅ ТЕСТ TELEGRAM ВОССТАНОВЛЕНИЯ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_telegram_recovery() 