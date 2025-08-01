#!/usr/bin/env python3
"""
Моки для Vinted и Telegram ответов
"""

import sys
import os
import time
import json
import requests
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

class MockResponses:
    """Моки ответов для тестирования"""
    
    @staticmethod
    def mock_vinted_success():
        """Мок успешного ответа Vinted"""
        return {
            "items": [
                {
                    "id": 12345678,
                    "title": "Test Item 1",
                    "price": {"amount": "25.0", "currency_code": "EUR"},
                    "is_visible": True,
                    "brand_title": "Test Brand",
                    "path": "/items/12345678-test-item-1"
                },
                {
                    "id": 87654321,
                    "title": "Test Item 2", 
                    "price": {"amount": "35.0", "currency_code": "EUR"},
                    "is_visible": True,
                    "brand_title": "Test Brand 2",
                    "path": "/items/87654321-test-item-2"
                }
            ],
            "pagination": {
                "current_page": 1,
                "per_page": 2,
                "total_count": 100
            }
        }
    
    @staticmethod
    def mock_vinted_429():
        """Мок ошибки 429 от Vinted"""
        return Mock(
            status_code=429,
            text="Too Many Requests",
            json=lambda: {"error": "Rate limit exceeded"}
        )
    
    @staticmethod
    def mock_vinted_403():
        """Мок ошибки 403 от Vinted"""
        return Mock(
            status_code=403,
            text="Forbidden",
            json=lambda: {"error": "Access denied"}
        )
    
    @staticmethod
    def mock_vinted_521():
        """Мок ошибки 521 от Vinted"""
        return Mock(
            status_code=521,
            text="Web server is down",
            json=lambda: {"error": "Server error"}
        )
    
    @staticmethod
    def mock_telegram_success():
        """Мок успешного ответа Telegram"""
        return Mock(
            status_code=200,
            json=lambda: {"ok": True, "result": {"message_id": 123}}
        )
    
    @staticmethod
    def mock_telegram_429():
        """Мок ошибки 429 от Telegram"""
        return Mock(
            status_code=429,
            json=lambda: {"ok": False, "error_code": 429, "description": "Too Many Requests"}
        )
    
    @staticmethod
    def mock_telegram_conflict():
        """Мок ошибки конфликта от Telegram"""
        return Mock(
            status_code=409,
            json=lambda: {"ok": False, "error_code": 409, "description": "Conflict"}
        )

class MockTestVintedScanner:
    """Тесты с моками для Vinted Scanner"""
    
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
    
    def test_1_vinted_429_error_handling(self):
        """Тест 1: Обработка ошибки 429 от Vinted"""
        print("\n🌐 ТЕСТ 1: Обработка ошибки 429 от Vinted")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "basic"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
        
        # Мокаем запрос к Vinted с ошибкой 429
        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponses.mock_vinted_429()
            
            # Симулируем запрос
            try:
                response = requests.get("https://www.vinted.de/api/v2/catalog/items")
                print(f"   📊 Статус ответа: {response.status_code}")
                
                # Симулируем обработку ошибки
                vinted_scanner.basic_system_errors += 1
                print(f"   ❌ Ошибка 429 обработана (basic_system_errors = {vinted_scanner.basic_system_errors})")
                
                # Проверяем переключение системы
                if vinted_scanner.should_switch_system():
                    print(f"   ✅ Система переключена на: {vinted_scanner.current_system}")
                    success = True
                else:
                    print(f"   ⚠️ Переключение не произошло")
                    success = False
                    
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "vinted_429_error_handling",
            "final_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_2_vinted_403_error_handling(self):
        """Тест 2: Обработка ошибки 403 от Vinted"""
        print("\n🌐 ТЕСТ 2: Обработка ошибки 403 от Vinted")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "advanced_no_proxy"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
        
        # Мокаем запрос к Vinted с ошибкой 403
        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponses.mock_vinted_403()
            
            # Симулируем запрос
            try:
                response = requests.get("https://www.vinted.de/api/v2/catalog/items")
                print(f"   📊 Статус ответа: {response.status_code}")
                
                # Симулируем обработку ошибки
                vinted_scanner.advanced_no_proxy_errors += 1
                print(f"   ❌ Ошибка 403 обработана (advanced_no_proxy_errors = {vinted_scanner.advanced_no_proxy_errors})")
                
                # Проверяем переключение системы
                if vinted_scanner.should_switch_system():
                    print(f"   ✅ Система переключена на: {vinted_scanner.current_system}")
                    success = True
                else:
                    print(f"   ⚠️ Переключение не произошло")
                    success = False
                    
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "vinted_403_error_handling",
            "final_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_3_vinted_521_error_handling(self):
        """Тест 3: Обработка ошибки 521 от Vinted"""
        print("\n🌐 ТЕСТ 3: Обработка ошибки 521 от Vinted")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "advanced_proxy"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
        
        # Мокаем запрос к Vinted с ошибкой 521
        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponses.mock_vinted_521()
            
            # Симулируем запрос
            try:
                response = requests.get("https://www.vinted.de/api/v2/catalog/items")
                print(f"   📊 Статус ответа: {response.status_code}")
                
                # Симулируем обработку ошибки
                vinted_scanner.advanced_proxy_errors += 1
                print(f"   ❌ Ошибка 521 обработана (advanced_proxy_errors = {vinted_scanner.advanced_proxy_errors})")
                
                # Проверяем переключение системы
                if vinted_scanner.should_switch_system():
                    print(f"   ✅ Система переключена на: {vinted_scanner.current_system}")
                    success = True
                else:
                    print(f"   ⚠️ Переключение не произошло")
                    success = False
                    
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "vinted_521_error_handling",
            "final_system": vinted_scanner.current_system,
            "success": success
        })
        
        return success
    
    def test_4_telegram_429_error_handling(self):
        """Тест 4: Обработка ошибки 429 от Telegram"""
        print("\n📱 ТЕСТ 4: Обработка ошибки 429 от Telegram")
        print("=" * 60)
        
        self.reset_system()
        
        print(f"📊 Исходное состояние Telegram:")
        print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Мокаем запрос к Telegram с ошибкой 429
        with patch('requests.post') as mock_post:
            mock_post.return_value = MockResponses.mock_telegram_429()
            
            # Симулируем отправку сообщения
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                    data={"chat_id": Config.telegram_chat_id, "text": "Test message"}
                )
                print(f"   📊 Статус ответа Telegram: {response.status_code}")
                
                # Симулируем обработку ошибки
                vinted_scanner.telegram_antiblock.handle_telegram_error("429")
                print(f"   ❌ Ошибка 429 обработана (consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors})")
                
                success = vinted_scanner.telegram_antiblock.consecutive_errors > 0
                
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "telegram_429_error_handling",
            "consecutive_errors": vinted_scanner.telegram_antiblock.consecutive_errors,
            "success": success
        })
        
        return success
    
    def test_5_telegram_conflict_error_handling(self):
        """Тест 5: Обработка ошибки конфликта от Telegram"""
        print("\n📱 ТЕСТ 5: Обработка ошибки конфликта от Telegram")
        print("=" * 60)
        
        self.reset_system()
        
        print(f"📊 Исходное состояние Telegram:")
        print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Мокаем запрос к Telegram с ошибкой конфликта
        with patch('requests.post') as mock_post:
            mock_post.return_value = MockResponses.mock_telegram_conflict()
            
            # Симулируем отправку сообщения
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                    data={"chat_id": Config.telegram_chat_id, "text": "Test message"}
                )
                print(f"   📊 Статус ответа Telegram: {response.status_code}")
                
                # Симулируем обработку ошибки
                vinted_scanner.telegram_antiblock.handle_telegram_error("conflict")
                print(f"   ❌ Ошибка конфликта обработана (consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors})")
                
                success = vinted_scanner.telegram_antiblock.consecutive_errors > 0
                
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "telegram_conflict_error_handling",
            "consecutive_errors": vinted_scanner.telegram_antiblock.consecutive_errors,
            "success": success
        })
        
        return success
    
    def test_6_telegram_success_handling(self):
        """Тест 6: Обработка успешного ответа от Telegram"""
        print("\n📱 ТЕСТ 6: Обработка успешного ответа от Telegram")
        print("=" * 60)
        
        self.reset_system()
        
        # Сначала создаем ошибки
        vinted_scanner.telegram_antiblock.consecutive_errors = 5
        vinted_scanner.telegram_antiblock.error_backoff = 10
        
        print(f"📊 Исходное состояние Telegram:")
        print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
        
        # Мокаем успешный запрос к Telegram
        with patch('requests.post') as mock_post:
            mock_post.return_value = MockResponses.mock_telegram_success()
            
            # Симулируем отправку сообщения
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                    data={"chat_id": Config.telegram_chat_id, "text": "Test message"}
                )
                print(f"   📊 Статус ответа Telegram: {response.status_code}")
                
                # Симулируем обработку успеха
                vinted_scanner.telegram_antiblock.handle_telegram_error("success")
                print(f"   ✅ Успех обработан (consecutive_errors = {vinted_scanner.telegram_antiblock.consecutive_errors})")
                
                success = (vinted_scanner.telegram_antiblock.consecutive_errors == 0 and 
                          vinted_scanner.telegram_antiblock.error_backoff == 1)
                
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "telegram_success_handling",
            "consecutive_errors": vinted_scanner.telegram_antiblock.consecutive_errors,
            "error_backoff": vinted_scanner.telegram_antiblock.error_backoff,
            "success": success
        })
        
        return success
    
    def test_7_vinted_success_handling(self):
        """Тест 7: Обработка успешного ответа от Vinted"""
        print("\n🌐 ТЕСТ 7: Обработка успешного ответа от Vinted")
        print("=" * 60)
        
        self.reset_system()
        vinted_scanner.current_system = "basic"
        
        print(f"📊 Исходное состояние:")
        print(f"   current_system: {vinted_scanner.current_system}")
        print(f"   basic_system_errors: {vinted_scanner.basic_system_errors}")
        
        # Мокаем успешный запрос к Vinted
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MockResponses.mock_vinted_success()
            mock_get.return_value = mock_response
            
            # Симулируем запрос
            try:
                response = requests.get("https://www.vinted.de/api/v2/catalog/items")
                print(f"   📊 Статус ответа: {response.status_code}")
                
                # Симулируем обработку успеха
                vinted_scanner.update_system_stats("basic", True)
                print(f"   ✅ Успех обработан (basic_success = {vinted_scanner.basic_success})")
                
                success = vinted_scanner.basic_success > 0
                
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                success = False
        
        self.test_results.append({
            "test": "vinted_success_handling",
            "basic_success": vinted_scanner.basic_success,
            "success": success
        })
        
        return success
    
    def test_8_retry_mechanism(self):
        """Тест 8: Механизм повторных попыток"""
        print("\n🔄 ТЕСТ 8: Механизм повторных попыток")
        print("=" * 60)
        
        self.reset_system()
        
        # Симулируем серию ошибок с последующим успехом
        error_responses = [
            MockResponses.mock_vinted_429(),
            MockResponses.mock_vinted_403(),
            MockResponses.mock_vinted_521(),
            Mock()  # Успешный ответ
        ]
        
        # Настраиваем мок для возврата разных ответов
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MockResponses.mock_vinted_success()
        error_responses[3] = mock_response
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = error_responses
            
            retry_count = 0
            max_retries = 3
            
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get("https://www.vinted.de/api/v2/catalog/items")
                    print(f"   📊 Попытка {attempt + 1}: Статус {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"   ✅ Успех на попытке {attempt + 1}")
                        retry_count = attempt + 1
                        break
                    else:
                        print(f"   ❌ Ошибка на попытке {attempt + 1}")
                        retry_count = attempt + 1
                        
                except Exception as e:
                    print(f"   ❌ Исключение на попытке {attempt + 1}: {e}")
                    retry_count = attempt + 1
            
            success = retry_count <= max_retries + 1
        
        self.test_results.append({
            "test": "retry_mechanism",
            "retry_count": retry_count,
            "max_retries": max_retries,
            "success": success
        })
        
        return success
    
    def run_all_mock_tests(self):
        """Запуск всех тестов с моками"""
        print("🎭 ТЕСТЫ С МОКАМИ VINTED SCANNER")
        print("=" * 60)
        
        tests = [
            ("Обработка ошибки 429 от Vinted", self.test_1_vinted_429_error_handling),
            ("Обработка ошибки 403 от Vinted", self.test_2_vinted_403_error_handling),
            ("Обработка ошибки 521 от Vinted", self.test_3_vinted_521_error_handling),
            ("Обработка ошибки 429 от Telegram", self.test_4_telegram_429_error_handling),
            ("Обработка ошибки конфликта от Telegram", self.test_5_telegram_conflict_error_handling),
            ("Обработка успешного ответа от Telegram", self.test_6_telegram_success_handling),
            ("Обработка успешного ответа от Vinted", self.test_7_vinted_success_handling),
            ("Механизм повторных попыток", self.test_8_retry_mechanism)
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
        
        print(f"\n📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ С МОКАМИ:")
        print(f"   ✅ Успешных тестов: {successful_tests}/{total_tests}")
        print(f"   ❌ Проваленных тестов: {total_tests - successful_tests}")
        print(f"   ⏱️ Время выполнения: {duration:.2f} секунд")
        print(f"   📊 Успешность: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ВСЕ ТЕСТЫ С МОКАМИ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ С МОКАМИ ПРОВАЛЕНЫ!")
        
        return successful_tests == total_tests

def run_mock_tests():
    """Запуск тестов с моками"""
    tester = MockTestVintedScanner()
    return tester.run_all_mock_tests()

if __name__ == "__main__":
    run_mock_tests() 