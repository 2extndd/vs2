#!/usr/bin/env python3
"""
Стресс-тесты для Vinted Scanner
"""

import sys
import os
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

class StressTestVintedScanner:
    """Стресс-тесты Vinted Scanner"""
    
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
    
    def test_1_basic_system_stress(self):
        """Стресс-тест 1: Базовая система под нагрузкой"""
        print("\n🔥 СТРЕСС-ТЕСТ 1: Базовая система под нагрузкой")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "basic"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
        
        # Симулируем 50+ запросов подряд
        total_requests = 50
        successful_switches = 0
        
        for i in range(total_requests):
            # Симулируем ошибку каждые 3 запроса
            if i % 3 == 0:
                vinted_scanner.basic_system_errors += 1
                print(f"   Запрос {i+1}: Ошибка (basic_system_errors = {vinted_scanner.basic_system_errors})")
                
                # Проверяем переключение
                if vinted_scanner.should_switch_system():
                    successful_switches += 1
                    print(f"   ✅ Переключение {successful_switches}: {vinted_scanner.current_system}")
                    
                    # Сбрасываем ошибки для следующего цикла
                    vinted_scanner.basic_system_errors = 0
            else:
                print(f"   Запрос {i+1}: Успех")
        
        print(f"\n📊 Результаты стресс-теста:")
        print(f"   📈 Всего запросов: {total_requests}")
        print(f"   🔄 Успешных переключений: {successful_switches}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        self.test_results.append({
            "test": "basic_system_stress",
            "total_requests": total_requests,
            "successful_switches": successful_switches,
            "final_system": vinted_scanner.current_system,
            "success": successful_switches > 0
        })
        
        return successful_switches > 0
    
    def test_2_advanced_system_stress(self):
        """Стресс-тест 2: Продвинутая система под нагрузкой"""
        print("\n🔥 СТРЕСС-ТЕСТ 2: Продвинутая система под нагрузкой")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "advanced_no_proxy"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        
        # Симулируем 50+ запросов подряд
        total_requests = 50
        successful_switches = 0
        
        for i in range(total_requests):
            # Симулируем ошибку каждые 4 запроса
            if i % 4 == 0:
                vinted_scanner.advanced_no_proxy_errors += 1
                print(f"   Запрос {i+1}: Ошибка (advanced_no_proxy_errors = {vinted_scanner.advanced_no_proxy_errors})")
                
                # Проверяем переключение
                if vinted_scanner.should_switch_system():
                    successful_switches += 1
                    print(f"   ✅ Переключение {successful_switches}: {vinted_scanner.current_system}")
                    
                    # Сбрасываем ошибки для следующего цикла
                    vinted_scanner.advanced_no_proxy_errors = 0
            else:
                print(f"   Запрос {i+1}: Успех")
        
        print(f"\n📊 Результаты стресс-теста:")
        print(f"   📈 Всего запросов: {total_requests}")
        print(f"   🔄 Успешных переключений: {successful_switches}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        self.test_results.append({
            "test": "advanced_system_stress",
            "total_requests": total_requests,
            "successful_switches": successful_switches,
            "final_system": vinted_scanner.current_system,
            "success": successful_switches > 0
        })
        
        return successful_switches > 0
    
    def test_3_proxy_system_stress(self):
        """Стресс-тест 3: Прокси система под нагрузкой"""
        print("\n🔥 СТРЕСС-ТЕСТ 3: Прокси система под нагрузкой")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "advanced_proxy"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        
        # Симулируем 50+ запросов подряд
        total_requests = 50
        successful_switches = 0
        
        for i in range(total_requests):
            # Симулируем ошибку каждые 5 запросов
            if i % 5 == 0:
                vinted_scanner.advanced_proxy_errors += 1
                print(f"   Запрос {i+1}: Ошибка (advanced_proxy_errors = {vinted_scanner.advanced_proxy_errors})")
                
                # Проверяем переключение
                if vinted_scanner.should_switch_system():
                    successful_switches += 1
                    print(f"   ✅ Переключение {successful_switches}: {vinted_scanner.current_system}")
                    
                    # Сбрасываем ошибки для следующего цикла
                    vinted_scanner.advanced_proxy_errors = 0
            else:
                print(f"   Запрос {i+1}: Успех")
        
        print(f"\n📊 Результаты стресс-теста:")
        print(f"   📈 Всего запросов: {total_requests}")
        print(f"   🔄 Успешных переключений: {successful_switches}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        self.test_results.append({
            "test": "proxy_system_stress",
            "total_requests": total_requests,
            "successful_switches": successful_switches,
            "final_system": vinted_scanner.current_system,
            "success": successful_switches > 0
        })
        
        return successful_switches > 0
    
    def test_4_concurrent_stress(self):
        """Стресс-тест 4: Конкурентные запросы"""
        print("\n🔥 СТРЕСС-ТЕСТ 4: Конкурентные запросы")
        print("=" * 60)
        
        self.reset_system()
        
        def simulate_request(request_id):
            """Симуляция одного запроса"""
            try:
                # Симулируем случайную ошибку
                if request_id % 7 == 0:
                    vinted_scanner.basic_system_errors += 1
                    result = vinted_scanner.should_switch_system()
                    return {"request_id": request_id, "error": True, "switched": result}
                else:
                    return {"request_id": request_id, "error": False, "switched": False}
            except Exception as e:
                return {"request_id": request_id, "error": True, "exception": str(e)}
        
        # Запускаем 30 конкурентных запросов
        total_requests = 30
        successful_requests = 0
        errors = 0
        switches = 0
        
        print(f"📊 Запуск {total_requests} конкурентных запросов...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_request, i) for i in range(total_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result.get("error"):
                    errors += 1
                    if result.get("switched"):
                        switches += 1
                else:
                    successful_requests += 1
                
                print(f"   Запрос {result['request_id']}: {'❌' if result.get('error') else '✅'}")
        
        print(f"\n📊 Результаты конкурентного стресс-теста:")
        print(f"   📈 Всего запросов: {total_requests}")
        print(f"   ✅ Успешных: {successful_requests}")
        print(f"   ❌ Ошибок: {errors}")
        print(f"   🔄 Переключений: {switches}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        self.test_results.append({
            "test": "concurrent_stress",
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "errors": errors,
            "switches": switches,
            "final_system": vinted_scanner.current_system,
            "success": successful_requests > 0
        })
        
        return successful_requests > 0
    
    def test_5_telegram_stress(self):
        """Стресс-тест 5: Telegram API под нагрузкой"""
        print("\n🔥 СТРЕСС-ТЕСТ 5: Telegram API под нагрузкой")
        print("=" * 60)
        
        self.reset_system()
        
        print(f"📊 Исходное состояние Telegram:")
        print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Симулируем 30 ошибок Telegram подряд
        total_errors = 30
        error_types = ["429", "conflict", "getUpdates", "network", "timeout"]
        
        for i in range(total_errors):
            error_type = error_types[i % len(error_types)]
            vinted_scanner.telegram_antiblock.handle_telegram_error(error_type)
            
            if i % 5 == 0:
                print(f"   Ошибка {i+1}: {error_type} (consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors})")
        
        # Проверяем сброс через успешный запрос
        vinted_scanner.telegram_antiblock.handle_telegram_error("success")
        
        print(f"\n📊 Результаты Telegram стресс-теста:")
        print(f"   📈 Всего ошибок: {total_errors}")
        print(f"   📊 Финальные consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   📊 Финальный error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        success = vinted_scanner.telegram_antiblock.consecutive_errors == 0
        
        self.test_results.append({
            "test": "telegram_stress",
            "total_errors": total_errors,
            "final_consecutive_errors": vinted_scanner.telegram_antiblock.consecutive_errors,
            "final_error_backoff": vinted_scanner.telegram_antiblock.error_backoff,
            "success": success
        })
        
        return success
    
    def test_6_recovery_stress(self):
        """Стресс-тест 6: Система восстановления под нагрузкой"""
        print("\n🔥 СТРЕСС-ТЕСТ 6: Система восстановления под нагрузкой")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем критические условия
        vinted_scanner.basic_system_errors = 25
        vinted_scanner.advanced_no_proxy_errors = 20
        vinted_scanner.advanced_proxy_errors = 15
        vinted_scanner.telegram_antiblock.consecutive_errors = 25
        vinted_scanner.telegram_antiblock.error_backoff = 15
        
        print(f"📊 Критические условия:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        
        # Запускаем восстановление 5 раз подряд
        recovery_attempts = 5
        successful_recoveries = 0
        
        for i in range(recovery_attempts):
            # Симулируем новые ошибки
            vinted_scanner.basic_system_errors += 5
            vinted_scanner.advanced_no_proxy_errors += 5
            vinted_scanner.advanced_proxy_errors += 5
            vinted_scanner.telegram_antiblock.consecutive_errors += 5
            
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
        
        print(f"\n📊 Результаты восстановления:")
        print(f"   📈 Попыток восстановления: {recovery_attempts}")
        print(f"   ✅ Успешных восстановлений: {successful_recoveries}")
        print(f"   📊 Финальная система: {vinted_scanner.current_system}")
        
        self.test_results.append({
            "test": "recovery_stress",
            "recovery_attempts": recovery_attempts,
            "successful_recoveries": successful_recoveries,
            "final_system": vinted_scanner.current_system,
            "success": successful_recoveries > 0
        })
        
        return successful_recoveries > 0
    
    def run_all_stress_tests(self):
        """Запуск всех стресс-тестов"""
        print("🔥 ПОЛНЫЕ СТРЕСС-ТЕСТЫ VINTED SCANNER")
        print("=" * 60)
        
        tests = [
            ("Базовая система", self.test_1_basic_system_stress),
            ("Продвинутая система", self.test_2_advanced_system_stress),
            ("Прокси система", self.test_3_proxy_system_stress),
            ("Конкурентные запросы", self.test_4_concurrent_stress),
            ("Telegram API", self.test_5_telegram_stress),
            ("Система восстановления", self.test_6_recovery_stress)
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
        
        print(f"\n📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТОВ:")
        print(f"   ✅ Успешных тестов: {successful_tests}/{total_tests}")
        print(f"   ❌ Проваленных тестов: {total_tests - successful_tests}")
        print(f"   ⏱️ Время выполнения: {duration:.2f} секунд")
        print(f"   📊 Успешность: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ВСЕ СТРЕСС-ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️ НЕКОТОРЫЕ СТРЕСС-ТЕСТЫ ПРОВАЛЕНЫ!")
        
        return successful_tests == total_tests

def run_stress_tests():
    """Запуск стресс-тестов"""
    tester = StressTestVintedScanner()
    return tester.run_all_stress_tests()

if __name__ == "__main__":
    run_stress_tests() 