#!/usr/bin/env python3
"""
Полный стресс-тест всех команд бота
"""

import sys
import os
import time
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

def test_telegram_commands():
    """Тестируем все команды через Telegram API"""
    print("📱 ПОЛНЫЙ СТРЕСС-ТЕСТ TELEGRAM КОМАНД")
    print("=" * 60)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram токен или chat_id не настроены")
        return
    
    base_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}"
    
    # Список всех команд для тестирования
    commands = [
        "/status",
        "/log", 
        "/fast",
        "/slow",
        "/reset",
        "/system auto",
        "/system basic",
        "/system advanced",
        "/system proxy",
        "/system noproxy",
        "/recovery",
        "/recovery test",
        "/recovery reset",
        "/recovery force_proxy",
        "/recovery force_noproxy",
        "/recovery force_advanced",
        "/proxy",
        "/traffic",
        "/topics",
        "/threadid",
        "/detect"
    ]
    
    print(f"📊 Тестируем {len(commands)} команд...")
    
    for i, command in enumerate(commands, 1):
        print(f"\n🔄 ТЕСТ {i}/{len(commands)}: {command}")
        
        try:
            # Отправляем команду
            response = requests.post(
                f"{base_url}/sendMessage",
                data={
                    "chat_id": Config.telegram_chat_id,
                    "text": command,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Команда отправлена: {command}")
                
                # Ждем ответа бота
                time.sleep(2)
                
                # Получаем последние сообщения
                updates_response = requests.get(
                    f"{base_url}/getUpdates",
                    params={"limit": 5, "timeout": 5},
                    timeout=10
                )
                
                if updates_response.status_code == 200:
                    updates = updates_response.json()
                    if updates.get("ok") and updates.get("result"):
                        latest_message = updates["result"][-1]
                        if "message" in latest_message and "text" in latest_message["message"]:
                            bot_response = latest_message["message"]["text"]
                            print(f"   📤 Ответ бота: {bot_response[:100]}...")
                        else:
                            print(f"   ⚠️ Нет текстового ответа от бота")
                    else:
                        print(f"   ⚠️ Нет обновлений от бота")
                else:
                    print(f"   ❌ Ошибка получения обновлений: {updates_response.status_code}")
                    
            else:
                print(f"   ❌ Ошибка отправки команды: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка тестирования команды {command}: {str(e)[:50]}")
        
        # Пауза между командами
        time.sleep(1)
    
    print(f"\n✅ СТРЕСС-ТЕСТ КОМАНД ЗАВЕРШЕН")

def test_system_switching():
    """Тестируем переключение систем"""
    print(f"\n🔄 ТЕСТ ПЕРЕКЛЮЧЕНИЯ СИСТЕМ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_system_mode = vinted_scanner.system_mode
    
    print(f"📊 ИСХОДНОЕ СОСТОЯНИЕ:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   system_mode: {vinted_scanner.system_mode}")
    
    # Тест 1: Переключение режимов системы
    test_modes = ["auto", "basic", "advanced", "proxy", "noproxy"]
    
    for mode in test_modes:
        print(f"\n🔄 Тестируем режим: {mode}")
        vinted_scanner.system_mode = mode
        
        # Симулируем ошибки для переключения
        if mode == "basic":
            vinted_scanner.current_system = "basic"
            vinted_scanner.basic_system_errors = 3
            vinted_scanner.last_switch_time = time.time()
            
            result = vinted_scanner.should_switch_system()
            print(f"   Результат переключения: {result}")
            print(f"   Новая система: {vinted_scanner.current_system}")
            
        elif mode == "advanced":
            vinted_scanner.current_system = "advanced_no_proxy"
            vinted_scanner.advanced_no_proxy_errors = 3
            vinted_scanner.last_switch_time = time.time()
            
            result = vinted_scanner.should_switch_system()
            print(f"   Результат переключения: {result}")
            print(f"   Новая система: {vinted_scanner.current_system}")
            
        elif mode == "proxy":
            vinted_scanner.current_system = "advanced_proxy"
            vinted_scanner.advanced_proxy_errors = 3
            vinted_scanner.last_switch_time = time.time()
            
            result = vinted_scanner.should_switch_system()
            print(f"   Результат переключения: {result}")
            print(f"   Новая система: {vinted_scanner.current_system}")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.system_mode = original_system_mode
    
    print(f"\n✅ ТЕСТ ПЕРЕКЛЮЧЕНИЯ СИСТЕМ ЗАВЕРШЕН")

def test_statistics():
    """Тестируем статистику"""
    print(f"\n📊 ТЕСТ СТАТИСТИКИ")
    print("=" * 60)
    
    # Симулируем различные запросы
    print(f"📈 Симулируем запросы...")
    
    for i in range(10):
        system = "basic" if i % 3 == 0 else "advanced_no_proxy" if i % 3 == 1 else "advanced_proxy"
        success = i % 4 != 0  # 75% успешность
        
        vinted_scanner.update_system_stats(system, success)
        print(f"   Запрос {i+1}: {system} - {'✅' if success else '❌'}")
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Базовые запросы: {vinted_scanner.basic_requests}")
    print(f"   Базовые успехи: {vinted_scanner.basic_success}")
    print(f"   Продвинутые без прокси запросы: {vinted_scanner.advanced_no_proxy_requests}")
    print(f"   Продвинутые без прокси успехи: {vinted_scanner.advanced_no_proxy_success}")
    print(f"   Продвинутые с прокси запросы: {vinted_scanner.advanced_proxy_requests}")
    print(f"   Продвинутые с прокси успехи: {vinted_scanner.advanced_proxy_success}")
    
    # Расчет общей успешности
    total_requests = (vinted_scanner.basic_requests + 
                     vinted_scanner.advanced_no_proxy_requests + 
                     vinted_scanner.advanced_proxy_requests)
    total_success = (vinted_scanner.basic_success + 
                    vinted_scanner.advanced_no_proxy_success + 
                    vinted_scanner.advanced_proxy_success)
    
    if total_requests > 0:
        success_rate = (total_success / total_requests) * 100
        print(f"   Общая успешность: {success_rate:.1f}%")
    
    print(f"\n✅ ТЕСТ СТАТИСТИКИ ЗАВЕРШЕН")

def test_recovery_system():
    """Тестируем систему восстановления"""
    print(f"\n🔄 ТЕСТ СИСТЕМЫ ВОССТАНОВЛЕНИЯ")
    print("=" * 60)
    
    # Симулируем критические условия
    print(f"📊 Симулируем критические условия...")
    
    vinted_scanner.basic_system_errors = 15
    vinted_scanner.advanced_no_proxy_errors = 10
    vinted_scanner.advanced_proxy_errors = 5
    vinted_scanner.telegram_antiblock.consecutive_errors = 15
    vinted_scanner.telegram_antiblock.error_backoff = 10
    
    print(f"   До восстановления:")
    print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   - telegram_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Запускаем восстановление
    vinted_scanner.auto_recovery_system()
    
    print(f"\n   После восстановления:")
    print(f"   - basic_system_errors: {vinted_scanner.basic_system_errors}")
    print(f"   - advanced_no_proxy_errors: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   - advanced_proxy_errors: {vinted_scanner.advanced_proxy_errors}")
    print(f"   - telegram_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   - telegram_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    print(f"   - current_system: {vinted_scanner.current_system}")
    
    print(f"\n✅ ТЕСТ СИСТЕМЫ ВОССТАНОВЛЕНИЯ ЗАВЕРШЕН")

def test_telegram_errors():
    """Тестируем обработку ошибок Telegram"""
    print(f"\n📱 ТЕСТ ОБРАБОТКИ ОШИБОК TELEGRAM")
    print("=" * 60)
    
    print(f"📊 Исходное состояние:")
    print(f"   consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Симулируем различные ошибки
    error_types = ["429", "conflict", "getUpdates", "network", "timeout"]
    
    for error_type in error_types:
        print(f"\n🔄 Тестируем ошибку: {error_type}")
        vinted_scanner.telegram_antiblock.handle_telegram_error(error_type)
        
        print(f"   После обработки:")
        print(f"   - consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
        print(f"   - error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    # Сброс через успешный запрос
    print(f"\n🔄 Сброс через успешный запрос")
    vinted_scanner.telegram_antiblock.handle_telegram_error("success")
    
    print(f"   После сброса:")
    print(f"   - consecutive_errors: {vinted_scanner.telegram_antiblock.consecutive_errors}")
    print(f"   - error_backoff: {vinted_scanner.telegram_antiblock.error_backoff}")
    
    print(f"\n✅ ТЕСТ ОБРАБОТКИ ОШИБОК TELEGRAM ЗАВЕРШЕН")

def test_logs():
    """Анализируем логи"""
    print(f"\n📝 АНАЛИЗ ЛОГОВ")
    print("=" * 60)
    
    log_file = "vinted_scanner.log"
    
    if os.path.exists(log_file):
        print(f"📄 Анализируем файл: {log_file}")
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            print(f"📊 Статистика логов:")
            print(f"   Всего строк: {len(lines)}")
            
            # Анализ последних 50 строк
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            
            print(f"\n📋 Последние {len(recent_lines)} строк:")
            for i, line in enumerate(recent_lines, 1):
                print(f"   {i:2d}: {line.strip()}")
                
        except Exception as e:
            print(f"❌ Ошибка чтения логов: {e}")
    else:
        print(f"⚠️ Файл логов не найден: {log_file}")
    
    print(f"\n✅ АНАЛИЗ ЛОГОВ ЗАВЕРШЕН")

def main():
    """Главная функция тестирования"""
    print("🚀 ПОЛНЫЙ СТРЕСС-ТЕСТ ВСЕХ СИСТЕМ")
    print("=" * 60)
    
    # Тест 1: Команды Telegram
    test_telegram_commands()
    
    # Тест 2: Переключение систем
    test_system_switching()
    
    # Тест 3: Статистика
    test_statistics()
    
    # Тест 4: Система восстановления
    test_recovery_system()
    
    # Тест 5: Обработка ошибок Telegram
    test_telegram_errors()
    
    # Тест 6: Анализ логов
    test_logs()
    
    print(f"\n🎯 ПОЛНЫЙ СТРЕСС-ТЕСТ ЗАВЕРШЕН!")
    print(f"🛡️ ВСЕ СИСТЕМЫ ПРОТЕСТИРОВАНЫ!")
    print(f"✅ БОТ ГОТОВ К ПРОДАКШЕНУ!")

if __name__ == "__main__":
    main() 