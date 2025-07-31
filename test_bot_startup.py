#!/usr/bin/env python3
"""
Тест запуска бота с системой резервирования
"""

import sys
import time
import Config
from vinted_scanner import reservation_system, setup_bot

def test_bot_startup():
    """Тест запуска бота"""
    print("🧪 Тест запуска бота с системой резервирования")
    print("=" * 50)
    
    # Проверяем конфигурацию
    print("\n📋 Проверка конфигурации:")
    print(f"  Telegram Token: {'✅' if Config.telegram_bot_token else '❌'}")
    print(f"  Chat ID: {'✅' if Config.telegram_chat_id else '❌'}")
    print(f"  Vinted URL: {'✅' if Config.vinted_url else '❌'}")
    print(f"  Резервирование: {'✅' if Config.reservation_enabled else '❌'}")
    
    # Проверяем систему резервирования
    print("\n🔧 Проверка системы резервирования:")
    print(f"  Система создана: {'✅' if reservation_system else '❌'}")
    print(f"  Активных резервирований: {len(reservation_system.reserved_items)}")
    
    # Проверяем команды
    print("\n📋 Проверка команд:")
    try:
        # Проверяем наличие функций команд
        from vinted_scanner import unified_reserve_command, reservation_status_command
        
        print(f"  ✅ unified_reserve_command: найдена")
        print(f"  ✅ reservation_status_command: найдена")
        print(f"  ✅ Команды резервирования: доступны")
            
    except Exception as e:
        print(f"  ❌ Ошибка проверки команд: {str(e)[:50]}")
    
    # Проверяем импорты
    print("\n📦 Проверка импортов:")
    required_modules = [
        'requests',
        'telegram',
        'asyncio',
        'logging',
        'time',
        'random',
        'json'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    if Config.telegram_bot_token and Config.telegram_chat_id:
        print("✅ Конфигурация Telegram: ГОТОВА")
    else:
        print("❌ Конфигурация Telegram: НЕПОЛНАЯ")
    
    if Config.reservation_enabled:
        print("✅ Система резервирования: ВКЛЮЧЕНА")
    else:
        print("❌ Система резервирования: ОТКЛЮЧЕНА")
    
    if reservation_system:
        print("✅ Система резервирования: ИНИЦИАЛИЗИРОВАНА")
    else:
        print("❌ Система резервирования: НЕ ИНИЦИАЛИЗИРОВАНА")
    
    print("\n🎯 Рекомендации:")
    if not Config.telegram_bot_token:
        print("  - Укажите telegram_bot_token в Config.py")
    if not Config.telegram_chat_id:
        print("  - Укажите telegram_chat_id в Config.py")
    if not Config.reservation_enabled:
        print("  - Включите reservation_enabled = True в Config.py")
    
    print("\n🚀 Для запуска бота используйте:")
    print("  python3 vinted_scanner.py")
    
    return True

if __name__ == "__main__":
    test_bot_startup() 