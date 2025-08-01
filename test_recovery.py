#!/usr/bin/env python3
"""
Тесты восстановления для Vinted Scanner
"""

import sys
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

class RecoveryTestVintedScanner:
    """Тесты восстановления Vinted Scanner"""
    
    def __init__(self):
        """Инициализация тестов"""
        self.test_results = []
        self.start_time = time.time()
        
        # Сохраняем оригинальные значения
        self.original_scan_mode = vinted_scanner.scan_mode
        self.original_system_mode = vinted_scanner.system_mode
        self.original_current_system = vinted_scanner.current_system
        
        # Сбрасываем счетчики
        vinted_scanner.basic_system_errors = 0
        vinted_scanner.advanced_no_proxy_errors = 0
        vinted_scanner.advanced_proxy_errors = 0
        vinted_scanner.last_switch_time = time.time()
        
        # Инициализируем TelegramAntiBlock
        if not hasattr(vinted_scanner, 'telegram_antiblock'):
            vinted_scanner.telegram_antiblock = vinted_scanner.TelegramAntiBlock()
    
    def reset_system(self):
        """Сброс системы к исходному состоянию"""
        vinted_scanner.scan_mode = self.original_scan_mode
        vinted_scanner.system_mode = self.original_system_mode
        vinted_scanner.current_system = self.original_current_system
        vinted_scanner.basic_system_errors = 0
        vinted_scanner.advanced_no_proxy_errors = 0
        vinted_scanner.advanced_proxy_errors = 0
        vinted_scanner.telegram_antiblock.consecutive_errors = 0
        vinted_scanner.telegram_antiblock.error_backoff = 1
    
    def test_1_forced_switching_after_5_minutes(self):
        """Тест 1: Принудительное переключение через 5 минут"""
        print("\n🔄 ТЕСТ 1: Принудительное переключение через 5 минут")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "basic"
        vinted_scanner.last_switch_time = time.time() - 301  # 5 минут + 1 секунда
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
        print(f"   Время в системе: {time.time() - vinted_scanner.last_switch_time:.1f} секунд")
        
        # Проверяем принудительное переключение
        result = vinted_scanner.should_switch_system()
        
        print(f"📊 Результат:")
        print(f"   Результат переключения: {result}")
        print(f"   Новая система: {vinted_scanner.current_system}")
        print(f"   Новое время переключения: {vinted_scanner.last_switch_time}")
        
        success = result and vinted_scanner.current_system == "advanced_no_proxy"
        
        self.test_results.append({
            "test": "forced_switching_5min",
            "result": result,
            "new_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_2_counter_reset_at_20_errors(self):
        """Тест 2: Сброс счетчиков при 20+ ошибках"""
        print("\n🔄 ТЕСТ 2: Сброс счетчиков при 20+ ошибках")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем критические ошибки
        vinted_scanner.basic_system_errors = 15
        vinted_scanner.advanced_no_proxy_errors = 10
        vinted_scanner.advanced_proxy_errors = 5
        vinted_scanner.telegram_antiblock.consecutive_errors = 15
        vinted_scanner.telegram_antiblock.error_backoff = 10
        
        print(f"📊 До восстановления:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - telegram_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"📊 После восстановления:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - telegram_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        print(f"   - current_system: {vinted_scanner.current_system}")
        
        # Проверяем сброс всех счетчиков
        success = (
            vinted_scanner.basic_system_errors == 0 and
            vinted_scanner.advanced_no_proxy_errors == 0 and
            vinted_scanner.advanced_proxy_errors == 0 and
            vinted_scanner.telegram_antiblock.consecutive_errors == 0 and
            vinted_scanner.telegram_antiblock.error_backoff == 1
        )
        
        self.test_results.append({
            "test": "counter_reset_20_errors",
            "basic_errors_after": vinted_scanner.basic_system_errors,
            "advanced_no_proxy_errors_after": vinted_scanner.advanced_no_proxy_errors,
            "advanced_proxy_errors_after": vinted_scanner.advanced_proxy_errors,
            "telegram_errors_after": vinted_scanner.telegram_antiblock.consecutive_errors,
            "telegram_backoff_after": vinted_scanner.telegram_antiblock.error_backoff,
            "success": success
        })
        
        return success
    
    def test_3_system_stuck_detection(self):
        """Тест 3: Обнаружение застревания системы"""
        print("\n🔄 ТЕСТ 3: Обнаружение застревания системы")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем застревание в системе на 30+ минут
        vinted_scanner.current_system = "basic"
        vinted_scanner.last_switch_time = time.time() - 1801  # 30 минут + 1 секунда
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
        print(f"   Время в системе: {time.time() - vinted_scanner.last_switch_time:.1f} секунд")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"📊 После восстановления:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   last_switch_time: {vinted_scanner.last_switch_time}")
        
        # Проверяем переключение на продвинутую систему
        success = vinted_scanner.current_system == "advanced_no_proxy"
        
        self.test_results.append({
            "test": "system_stuck_detection",
            "original_system": "basic",
            "new_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_4_telegram_error_recovery(self):
        """Тест 4: Восстановление ошибок Telegram"""
        print("\n🔄 ТЕСТ 4: Восстановление ошибок Telegram")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем множество ошибок Telegram
        vinted_scanner.telegram_antiblock.consecutive_errors = 25
        vinted_scanner.telegram_antiblock.error_backoff = 15
        
        print(f"📊 До восстановления:")
        print(f"   - consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"📊 После восстановления:")
        print(f"   - consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Проверяем сброс ошибок Telegram
        success = (
            vinted_scanner.telegram_antiblock.consecutive_errors == 0 and
            vinted_scanner.telegram_antiblock.error_backoff == 1
        )
        
        self.test_results.append({
            "test": "telegram_error_recovery",
            "consecutive_errors_after": vinted_scanner.telegram_antiblock.consecutive_errors,
            "error_backoff_after": vinted_scanner.telegram_antiblock.error_backoff,
            "success": success
        })
        
        return success
    
    def test_5_proxy_failure_recovery(self):
        """Тест 5: Восстановление при падении прокси"""
        print("\n🔄 ТЕСТ 5: Восстановление при падении прокси")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "advanced_proxy"
        vinted_scanner.advanced_proxy_errors = 15
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"📊 После восстановления:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        
        # Проверяем переключение на без прокси
        success = (
            vinted_scanner.current_system == "advanced_no_proxy" and
            vinted_scanner.advanced_proxy_errors == 0
        )
        
        self.test_results.append({
            "test": "proxy_failure_recovery",
            "original_system": "advanced_proxy",
            "new_system": vinted_scanner.current_system,
            "proxy_errors_after": vinted_scanner.advanced_proxy_errors,
            "success": success
        })
        
        return success
    
    def test_6_critical_error_recovery(self):
        """Тест 6: Восстановление при критических ошибках"""
        print("\n🔄 ТЕСТ 6: Восстановление при критических ошибках")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем критические ошибки во всех системах
        vinted_scanner.basic_system_errors = 30
        vinted_scanner.advanced_no_proxy_errors = 25
        vinted_scanner.advanced_proxy_errors = 20
        vinted_scanner.telegram_antiblock.consecutive_errors = 30
        vinted_scanner.telegram_antiblock.error_backoff = 20
        
        print(f"📊 Критические условия:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"📊 После восстановления:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - current_system: {vinted_scanner.current_system}")
        
        # Проверяем полный сброс всех ошибок
        success = (
            vinted_scanner.basic_system_errors == 0 and
            vinted_scanner.advanced_no_proxy_errors == 0 and
            vinted_scanner.advanced_proxy_errors == 0 and
            vinted_scanner.telegram_antiblock.consecutive_errors == 0 and
            vinted_scanner.telegram_antiblock.error_backoff == 1
        )
        
        self.test_results.append({
            "test": "critical_error_recovery",
            "all_errors_reset": success,
            "final_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_7_sequential_recovery(self):
        """Тест 7: Последовательное восстановление"""
        print("\n🔄 ТЕСТ 7: Последовательное восстановление")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем серию восстановлений
        recovery_attempts = 5
        successful_recoveries = 0
        
        for i in range(recovery_attempts):
            # Симулируем новые ошибки
            vinted_scanner.basic_system_errors = 20 + i * 5
            vinted_scanner.advanced_no_proxy_errors = 15 + i * 5
            vinted_scanner.advanced_proxy_errors = 10 + i * 5
            vinted_scanner.telegram_antiblock.consecutive_errors = 20 + i * 5
            
            print(f"📊 Попытка восстановления {i+1}:")
            print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
            print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
            print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
            print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
            
            # Запускаем восстановление
            vinted_scanner.auto_recovery_system()
            
            # Проверяем успешность восстановления
            if (vinted_scanner.basic_system_errors == 0 and 
                vinted_scanner.advanced_no_proxy_errors == 0 and
                vinted_scanner.advanced_proxy_errors == 0 and
                vinted_scanner.telegram_antiblock.consecutive_errors == 0):
                successful_recoveries += 1
                print(f"   ✅ Восстановление {i+1}: Успешно")
            else:
                print(f"   ❌ Восстановление {i+1}: Неудачно")
        
        print(f"\n📊 Результаты последовательного восстановления:")
        print(f"   📈 Попыток восстановления: {recovery_attempts}")
        print(f"   ✅ Успешных восстановлений: {successful_recoveries}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        success = successful_recoveries == recovery_attempts
        
        self.test_results.append({
            "test": "sequential_recovery",
            "recovery_attempts": recovery_attempts,
            "successful_recoveries": successful_recoveries,
            "final_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def run_all_recovery_tests(self):
        """Запуск всех тестов восстановления"""
        print("🔄 ТЕСТЫ ВОССТАНОВЛЕНИЯ VINTED SCANNER")
        print("=" * 60)
        
        tests = [
            ("Принудительное переключение через 5 минут", self.test_1_forced_switching_after_5_minutes),
            ("Сброс счетчиков при 20+ ошибках", self.test_2_counter_reset_at_20_errors),
            ("Обнаружение застревания системы", self.test_3_system_stuck_detection),
            ("Восстановление ошибок Telegram", self.test_4_telegram_error_recovery),
            ("Восстановление при падении прокси", self.test_5_proxy_failure_recovery),
            ("Восстановление при критических ошибках", self.test_6_critical_error_recovery),
            ("Последовательное восстановление", self.test_7_sequential_recovery)
        ]
        
        successful_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Запуск: {test_name}")
                if test_func():
                    successful_tests += 1
                    print(f"   ✅ {test_name}: УСПЕШНО")
                else:
                    print(f"   ❌ {test_name}: ПРОВАЛЕН")
            except Exception as e:
                print(f"   ⚠️ {test_name}: ОШИБКА - {str(e)}")
        
        # Выводим итоговые результаты
        end_time = time.time()
        duration = end_time - self.start_time
        
        print(f"\n📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ ВОССТАНОВЛЕНИЯ:")
        print(f"   ✅ Успешных тестов: {successful_tests}/{total_tests}")
        print(f"   ❌ Проваленных тестов: {total_tests - successful_tests}")
        print(f"   ⏱️ Время выполнения: {duration:.2f} секунд")
        print(f"   📊 Успешность: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ВСЕ ТЕСТЫ ВОССТАНОВЛЕНИЯ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ВОССТАНОВЛЕНИЯ ПРОВАЛЕНЫ!")
        
        return successful_tests == total_tests

def run_recovery_tests():
    """Запуск тестов восстановления"""
    tester = RecoveryTestVintedScanner()
    return tester.run_all_recovery_tests()

if __name__ == "__main__":
    run_recovery_tests() 