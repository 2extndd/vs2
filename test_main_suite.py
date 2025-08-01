#!/usr/bin/env python3
"""
Основные тесты для Vinted Scanner
"""

import sys
import os
import time
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

class TestVintedScanner(unittest.TestCase):
    """Основные тесты Vinted Scanner"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Сохраняем оригинальные значения
        self.original_scan_mode = vinted_scanner.scan_mode
        self.original_system_mode = vinted_scanner.system_mode
        self.original_current_system = vinted_scanner.current_system
        self.original_basic_errors = vinted_scanner.basic_system_errors
        self.original_advanced_no_proxy_errors = vinted_scanner.advanced_no_proxy_errors
        self.original_advanced_proxy_errors = vinted_scanner.advanced_proxy_errors
        
        # Сбрасываем счетчики
        vinted_scanner.basic_system_errors = 0
        vinted_scanner.advanced_no_proxy_errors = 0
        vinted_scanner.advanced_proxy_errors = 0
        vinted_scanner.last_switch_time = time.time()
        
        # Инициализируем TelegramAntiBlock если не существует
        if not hasattr(vinted_scanner, 'telegram_antiblock'):
            vinted_scanner.telegram_antiblock = vinted_scanner.TelegramAntiBlock()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Восстанавливаем оригинальные значения
        vinted_scanner.scan_mode = self.original_scan_mode
        vinted_scanner.system_mode = self.original_system_mode
        vinted_scanner.current_system = self.original_current_system
        vinted_scanner.basic_system_errors = self.original_basic_errors
        vinted_scanner.advanced_no_proxy_errors = self.original_advanced_no_proxy_errors
        vinted_scanner.advanced_proxy_errors = self.original_advanced_proxy_errors
    
    def test_1_basic_system_switching(self):
        """Тест 1: Переключение базовой системы"""
        print("\n🔄 ТЕСТ 1: Переключение базовой системы")
        
        # Устанавливаем базовую систему
        vinted_scanner.current_system = "basic"
        vinted_scanner.basic_system_errors = 0
        
        # Симулируем ошибки
        for i in range(3):
            vinted_scanner.basic_system_errors += 1
            print(f"   Ошибка {i+1}: basic_system_errors = {vinted_scanner.basic_system_errors}")
        
        # Проверяем переключение
        result = vinted_scanner.should_switch_system()
        print(f"   Результат переключения: {result}")
        print(f"   Новая система: {vinted_scanner.current_system}")
        
        self.assertTrue(result)
        self.assertEqual(vinted_scanner.current_system, "advanced_no_proxy")
        self.assertEqual(vinted_scanner.basic_system_errors, 0)
    
    def test_2_advanced_system_switching(self):
        """Тест 2: Переключение продвинутой системы"""
        print("\n🔄 ТЕСТ 2: Переключение продвинутой системы")
        
        # Устанавливаем продвинутую без прокси
        vinted_scanner.current_system = "advanced_no_proxy"
        vinted_scanner.advanced_no_proxy_errors = 0
        
        # Симулируем ошибки
        for i in range(3):
            vinted_scanner.advanced_no_proxy_errors += 1
            print(f"   Ошибка {i+1}: advanced_no_proxy_errors = {vinted_scanner.advanced_no_proxy_errors}")
        
        # Проверяем переключение
        result = vinted_scanner.should_switch_system()
        print(f"   Результат переключения: {result}")
        print(f"   Новая система: {vinted_scanner.current_system}")
        
        self.assertTrue(result)
        self.assertEqual(vinted_scanner.current_system, "advanced_proxy")
        self.assertEqual(vinted_scanner.advanced_no_proxy_errors, 0)
    
    def test_3_proxy_system_switching(self):
        """Тест 3: Переключение прокси системы"""
        print("\n🔄 ТЕСТ 3: Переключение прокси системы")
        
        # Устанавливаем продвинутую с прокси
        vinted_scanner.current_system = "advanced_proxy"
        vinted_scanner.advanced_proxy_errors = 0
        
        # Симулируем ошибки
        for i in range(3):
            vinted_scanner.advanced_proxy_errors += 1
            print(f"   Ошибка {i+1}: advanced_proxy_errors = {vinted_scanner.advanced_proxy_errors}")
        
        # Проверяем переключение
        result = vinted_scanner.should_switch_system()
        print(f"   Результат переключения: {result}")
        print(f"   Новая система: {vinted_scanner.current_system}")
        
        self.assertTrue(result)
        self.assertEqual(vinted_scanner.current_system, "advanced_no_proxy")
        self.assertEqual(vinted_scanner.advanced_proxy_errors, 0)
    
    def test_4_time_based_switching(self):
        """Тест 4: Переключение по времени"""
        print("\n🔄 ТЕСТ 4: Переключение по времени")
        
        # Устанавливаем базовую систему с давним временем переключения
        vinted_scanner.current_system = "basic"
        vinted_scanner.last_switch_time = time.time() - 301  # 5 минут + 1 секунда
        
        # Проверяем принудительное переключение
        result = vinted_scanner.should_switch_system()
        print(f"   Результат переключения: {result}")
        print(f"   Новая система: {vinted_scanner.current_system}")
        
        self.assertTrue(result)
        self.assertEqual(vinted_scanner.current_system, "advanced_no_proxy")
    
    def test_5_scan_mode_switching(self):
        """Тест 5: Переключение режимов сканирования"""
        print("\n🔄 ТЕСТ 5: Переключение режимов сканирования")
        
        # Тест fast режима
        vinted_scanner.scan_mode = "fast"
        self.assertEqual(vinted_scanner.scan_mode, "fast")
        print(f"   ✅ Fast режим: {vinted_scanner.scan_mode}")
        
        # Тест slow режима
        vinted_scanner.scan_mode = "slow"
        self.assertEqual(vinted_scanner.scan_mode, "slow")
        print(f"   ✅ Slow режим: {vinted_scanner.scan_mode}")
    
    def test_6_system_mode_switching(self):
        """Тест 6: Переключение режимов системы"""
        print("\n🔄 ТЕСТ 6: Переключение режимов системы")
        
        test_modes = ["auto", "basic", "advanced", "proxy", "noproxy"]
        
        for mode in test_modes:
            vinted_scanner.system_mode = mode
            self.assertEqual(vinted_scanner.system_mode, mode)
            print(f"   ✅ Режим {mode}: {vinted_scanner.system_mode}")
    
    def test_7_statistics_tracking(self):
        """Тест 7: Отслеживание статистики"""
        print("\n📊 ТЕСТ 7: Отслеживание статистики")
        
        # Симулируем запросы
        systems = ["basic", "advanced_no_proxy", "advanced_proxy"]
        
        for i, system in enumerate(systems):
            success = i % 2 == 0  # Чередуем успехи и неудачи
            vinted_scanner.update_system_stats(system, success)
            print(f"   Запрос {i+1}: {system} - {'✅' if success else '❌'}")
        
        # Проверяем статистику
        print(f"   📊 Базовые запросы: {vinted_scanner.basic_requests}")
        print(f"   📊 Базовые успехи: {vinted_scanner.basic_success}")
        print(f"   📊 Продвинутые без прокси запросы: {vinted_scanner.advanced_no_proxy_requests}")
        print(f"   📊 Продвинутые без прокси успехи: {vinted_scanner.advanced_no_proxy_success}")
        print(f"   📊 Продвинутые с прокси запросы: {vinted_scanner.advanced_proxy_requests}")
        print(f"   📊 Продвинутые с прокси успехи: {vinted_scanner.advanced_proxy_success}")
        
        self.assertGreater(vinted_scanner.basic_requests, 0)
        self.assertGreater(vinted_scanner.advanced_no_proxy_requests, 0)
        self.assertGreater(vinted_scanner.advanced_proxy_requests, 0)
    
    def test_8_telegram_error_handling(self):
        """Тест 8: Обработка ошибок Telegram"""
        print("\n📱 ТЕСТ 8: Обработка ошибок Telegram")
        
        # Проверяем исходное состояние
        original_errors = vinted_scanner.telegram_antiblock.consecutive_errors
        original_backoff = vinted_scanner.telegram_antiblock.error_backoff
        
        print(f"   📊 Исходное состояние:")
        print(f"   - consecutive_errors: {original_errors}")
        print(f"   - error_backoff: {original_backoff}")
        
        # Симулируем ошибки
        error_types = ["429", "conflict", "getUpdates"]
        
        for error_type in error_types:
            vinted_scanner.telegram_antiblock.handle_telegram_error(error_type)
            print(f"   После {error_type}: consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors}")
        
        # Проверяем увеличение счетчика
        self.assertGreater(vinted_scanner.telegram_antiblock.consecutive_errors, original_errors)
        
        # Сбрасываем через успешный запрос
        vinted_scanner.telegram_antiblock.handle_telegram_error("success")
        print(f"   После сброса: consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors}")
        
        self.assertEqual(vinted_scanner.telegram_antiblock.consecutive_errors, 0)
    
    def test_9_auto_recovery_system(self):
        """Тест 9: Система автоматического восстановления"""
        print("\n🔄 ТЕСТ 9: Система автоматического восстановления")
        
        # Симулируем критические условия
        vinted_scanner.basic_system_errors = 15
        vinted_scanner.advanced_no_proxy_errors = 10
        vinted_scanner.advanced_proxy_errors = 5
        vinted_scanner.telegram_antiblock.consecutive_errors = 15
        vinted_scanner.telegram_antiblock.error_backoff = 10
        
        print(f"   📊 До восстановления:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        
        # Запускаем восстановление
        vinted_scanner.auto_recovery_system()
        
        print(f"   📊 После восстановления:")
        print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
        print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - current_system: {vinted_scanner.current_system}")
        
        # Проверяем сброс счетчиков
        self.assertEqual(vinted_scanner.basic_system_errors, 0)
        self.assertEqual(vinted_scanner.advanced_no_proxy_errors, 0)
        self.assertEqual(vinted_scanner.advanced_proxy_errors, 0)
        self.assertEqual(vinted_scanner.telegram_antiblock.consecutive_errors, 0)
        self.assertEqual(vinted_scanner.telegram_antiblock.error_backoff, 1)
    
    def test_10_command_handlers(self):
        """Тест 10: Обработчики команд"""
        print("\n📋 ТЕСТ 10: Обработчики команд")
        
        # Проверяем существование всех обработчиков
        handlers = [
            "status_command", "log_command", "restart_command",
            "fast_command", "slow_command", "reset_command",
            "proxy_command", "system_command", "recovery_command",
            "traffic_command", "topics_command", "threadid_command",
            "detect_threadid_command"
        ]
        
        for handler_name in handlers:
            handler = getattr(vinted_scanner, handler_name, None)
            if handler:
                print(f"   ✅ {handler_name} - существует")
                self.assertIsNotNone(handler)
            else:
                print(f"   ❌ {handler_name} - НЕ НАЙДЕН")
                self.fail(f"Handler {handler_name} not found")

def run_main_tests():
    """Запуск основных тестов"""
    print("🎯 ОСНОВНЫЕ ТЕСТЫ VINTED SCANNER")
    print("=" * 60)
    
    # Создаем тестовый набор
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVintedScanner)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результаты
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТОВ:")
    print(f"   ✅ Успешных: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Проваленных: {len(result.failures)}")
    print(f"   ⚠️ Ошибок: {len(result.errors)}")
    print(f"   📊 Всего: {result.testsRun}")
    
    if result.wasSuccessful():
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_main_tests() 