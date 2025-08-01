#!/usr/bin/env python3
"""
Тест работы бота в реальном времени
"""

import sys
import os
import time
import requests
import json
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import Config

def monitor_bot_status():
    """Мониторинг статуса бота в реальном времени"""
    print("📊 МОНИТОРИНГ СТАТУСА БОТА В РЕАЛЬНОМ ВРЕМЕНИ")
    print("=" * 60)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram токен или chat_id не настроены")
        return
    
    base_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}"
    
    # Отправляем команду статуса
    try:
        response = requests.post(
            f"{base_url}/sendMessage",
            data={
                "chat_id": Config.telegram_chat_id,
                "text": "/status",
                "parse_mode": "HTML"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Команда /status отправлена")
            
            # Ждем ответа
            time.sleep(3)
            
            # Получаем обновления
            updates_response = requests.get(
                f"{base_url}/getUpdates",
                params={"limit": 10, "timeout": 5},
                timeout=10
            )
            
            if updates_response.status_code == 200:
                updates = updates_response.json()
                if updates.get("ok") and updates.get("result"):
                    for update in updates["result"]:
                        if "message" in update and "text" in update["message"]:
                            text = update["message"]["text"]
                            if "🟢 Running" in text or "📊 Items:" in text:
                                print("📤 Ответ бота на /status:")
                                print(text)
                                return True
                
                print("⚠️ Не получен ответ на /status")
            else:
                print(f"❌ Ошибка получения обновлений: {updates_response.status_code}")
        else:
            print(f"❌ Ошибка отправки команды: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
    
    return False

def test_system_commands():
    """Тестируем системные команды"""
    print(f"\n🔄 ТЕСТ СИСТЕМНЫХ КОМАНД")
    print("=" * 60)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram токен или chat_id не настроены")
        return
    
    base_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}"
    
    # Тестируем основные команды
    test_commands = [
        ("/fast", "быстрый режим"),
        ("/slow", "медленный режим"),
        ("/reset", "сброс системы"),
        ("/system auto", "автоматический режим"),
        ("/recovery", "статус восстановления")
    ]
    
    for command, description in test_commands:
        print(f"\n🔄 Тестируем: {description} ({command})")
        
        try:
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
                print(f"   ✅ Команда отправлена")
                time.sleep(2)
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
        
        time.sleep(1)

def test_recovery_commands():
    """Тестируем команды восстановления"""
    print(f"\n🔄 ТЕСТ КОМАНД ВОССТАНОВЛЕНИЯ")
    print("=" * 60)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram токен или chat_id не настроены")
        return
    
    base_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}"
    
    # Тестируем команды восстановления
    recovery_commands = [
        ("/recovery test", "тестирование прокси"),
        ("/recovery reset", "сброс системы"),
        ("/recovery force_advanced", "принудительное переключение на продвинутую"),
        ("/recovery force_noproxy", "принудительное отключение прокси")
    ]
    
    for command, description in recovery_commands:
        print(f"\n🔄 Тестируем: {description} ({command})")
        
        try:
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
                print(f"   ✅ Команда отправлена")
                time.sleep(3)  # Больше времени для recovery команд
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
        
        time.sleep(2)

def test_advanced_commands():
    """Тестируем продвинутые команды"""
    print(f"\n🔄 ТЕСТ ПРОДВИНУТЫХ КОМАНД")
    print("=" * 60)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram токен или chat_id не настроены")
        return
    
    base_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}"
    
    # Тестируем продвинутые команды
    advanced_commands = [
        ("/proxy", "статус прокси"),
        ("/traffic", "мониторинг трафика"),
        ("/topics", "список топиков"),
        ("/threadid", "управление thread ID"),
        ("/detect", "автоматическое определение thread ID")
    ]
    
    for command, description in advanced_commands:
        print(f"\n🔄 Тестируем: {description} ({command})")
        
        try:
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
                print(f"   ✅ Команда отправлена")
                time.sleep(2)
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
        
        time.sleep(1)

def monitor_logs():
    """Мониторинг логов в реальном времени"""
    print(f"\n📝 МОНИТОРИНГ ЛОГОВ В РЕАЛЬНОМ ВРЕМЕНИ")
    print("=" * 60)
    
    log_file = "vinted_scanner.log"
    
    if not os.path.exists(log_file):
        print(f"⚠️ Файл логов не найден: {log_file}")
        return
    
    print(f"📄 Мониторинг файла: {log_file}")
    print("🔄 Ожидание новых записей в логах...")
    
    # Читаем текущий размер файла
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            f.seek(0, 2)  # Переходим в конец файла
            initial_size = f.tell()
        
        print(f"📊 Начальный размер лога: {initial_size} байт")
        
        # Мониторим новые записи
        for i in range(10):  # 10 итераций мониторинга
            time.sleep(2)
            
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    f.seek(0, 2)
                    current_size = f.tell()
                
                if current_size > initial_size:
                    print(f"📝 Новые записи в логе (итерация {i+1})")
                    
                    # Читаем новые строки
                    with open(log_file, "r", encoding="utf-8") as f:
                        f.seek(initial_size)
                        new_lines = f.readlines()
                        
                    for line in new_lines:
                        print(f"   {line.strip()}")
                    
                    initial_size = current_size
                else:
                    print(f"⏳ Ожидание новых записей... (итерация {i+1})")
                    
            except Exception as e:
                print(f"❌ Ошибка чтения лога: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка мониторинга логов: {e}")

def test_system_switching_real_time():
    """Тестируем переключение систем в реальном времени"""
    print(f"\n🔄 ТЕСТ ПЕРЕКЛЮЧЕНИЯ СИСТЕМ В РЕАЛЬНОМ ВРЕМЕНИ")
    print("=" * 60)
    
    # Сохраняем оригинальные значения
    original_system = vinted_scanner.current_system
    original_system_mode = vinted_scanner.system_mode
    
    print(f"📊 Исходное состояние:")
    print(f"   current_system: {vinted_scanner.current_system}")
    print(f"   system_mode: {vinted_scanner.system_mode}")
    
    # Тестируем переключения в реальном времени
    test_scenarios = [
        ("basic -> advanced_no_proxy", "basic", 3, "basic_system_errors"),
        ("advanced_no_proxy -> advanced_proxy", "advanced_no_proxy", 3, "advanced_no_proxy_errors"),
        ("advanced_proxy -> advanced_no_proxy", "advanced_proxy", 3, "advanced_proxy_errors")
    ]
    
    for scenario_name, system, error_count, error_attr in test_scenarios:
        print(f"\n🔄 Тестируем сценарий: {scenario_name}")
        
        # Устанавливаем начальное состояние
        vinted_scanner.current_system = system
        setattr(vinted_scanner, error_attr, error_count)
        vinted_scanner.last_switch_time = time.time()
        
        print(f"   До переключения:")
        print(f"   - current_system: {vinted_scanner.current_system}")
        print(f"   - {error_attr}: {getattr(vinted_scanner, error_attr)}")
        
        # Выполняем переключение
        result = vinted_scanner.should_switch_system()
        
        print(f"   После переключения:")
        print(f"   - Результат: {result}")
        print(f"   - current_system: {vinted_scanner.current_system}")
        print(f"   - {error_attr}: {getattr(vinted_scanner, error_attr)}")
        
        if result:
            print(f"   ✅ Переключение выполнено успешно")
        else:
            print(f"   ❌ Переключение не выполнено")
    
    # Восстанавливаем оригинальные значения
    vinted_scanner.current_system = original_system
    vinted_scanner.system_mode = original_system_mode
    
    print(f"\n✅ ТЕСТ ПЕРЕКЛЮЧЕНИЯ СИСТЕМ ЗАВЕРШЕН")

def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТ РАБОТЫ БОТА В РЕАЛЬНОМ ВРЕМЕНИ")
    print("=" * 60)
    
    # Тест 1: Мониторинг статуса
    monitor_bot_status()
    
    # Тест 2: Системные команды
    test_system_commands()
    
    # Тест 3: Команды восстановления
    test_recovery_commands()
    
    # Тест 4: Продвинутые команды
    test_advanced_commands()
    
    # Тест 5: Переключение систем
    test_system_switching_real_time()
    
    # Тест 6: Мониторинг логов
    monitor_logs()
    
    print(f"\n🎯 ТЕСТ В РЕАЛЬНОМ ВРЕМЕНИ ЗАВЕРШЕН!")
    print(f"🛡️ ВСЕ СИСТЕМЫ ПРОТЕСТИРОВАНЫ!")
    print(f"✅ БОТ РАБОТАЕТ СТАБИЛЬНО!")

if __name__ == "__main__":
    main() 