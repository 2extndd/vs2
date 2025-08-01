#!/usr/bin/env python3
"""
Тест обновленных команд бота
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_updated_commands():
    """Тест обновленных команд"""
    print("🎯 ТЕСТ ОБНОВЛЕННЫХ КОМАНД БОТА")
    print("=" * 60)
    
    # Проверяем доступность продвинутой системы
    try:
        from advanced_antiban import get_advanced_system
        advanced_system = get_advanced_system()
        print("✅ Продвинутая система доступна")
    except ImportError as e:
        print(f"❌ Продвинутая система недоступна: {e}")
        return
    
    # Проверяем функции команд
    commands_to_test = [
        "status_command",
        "log_command", 
        "restart_command",
        "fast_command",
        "slow_command",
        "recovery_command",
        "proxy_command"
    ]
    
    print(f"\n📋 ПРОВЕРКА КОМАНД:")
    print("-" * 40)
    
    found_commands = 0
    for command in commands_to_test:
        try:
            # Импортируем функцию из vinted_scanner
            import vinted_scanner
            if hasattr(vinted_scanner, command):
                print(f"✅ {command} - найдена")
                found_commands += 1
            else:
                print(f"❌ {command} - не найдена")
        except Exception as e:
            print(f"❌ {command} - ошибка: {e}")
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"✅ Найдено команд: {found_commands}")
    print(f"❌ Отсутствует команд: {len(commands_to_test) - found_commands}")
    
    # Проверяем регистрацию команд в setup_bot
    print(f"\n🔧 ПРОВЕРКА РЕГИСТРАЦИИ КОМАНД:")
    print("-" * 40)
    
    try:
        import vinted_scanner
        setup_bot_source = vinted_scanner.setup_bot.__code__.co_consts
        
        # Ищем зарегистрированные команды
        registered_commands = []
        for const in setup_bot_source:
            if isinstance(const, str) and const.startswith('/'):
                registered_commands.append(const)
        
        print(f"📋 ЗАРЕГИСТРИРОВАННЫЕ КОМАНДЫ:")
        for cmd in registered_commands:
            print(f"• {cmd}")
            
        print(f"\n📊 ИТОГО КОМАНД: {len(registered_commands)}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки регистрации: {e}")
    
    # Проверяем функциональность продвинутой системы
    print(f"\n🧠 ПРОВЕРКА ПРОДВИНУТОЙ СИСТЕМЫ:")
    print("-" * 40)
    
    try:
        stats = advanced_system.get_stats()
        print("✅ Статистика получена успешно")
        print(f"📊 HTTP запросы: {stats.get('http_success', 0)}/{stats.get('http_requests', 0)}")
        print(f"📈 Успешность: {stats.get('success_rate', 0):.1f}%")
        print(f"📡 Прокси: {stats.get('proxies_count', 0)} активных")
        print(f"🔄 Режим: {stats.get('proxy_mode', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН!")

if __name__ == "__main__":
    test_updated_commands() 