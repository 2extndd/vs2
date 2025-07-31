#!/usr/bin/env python3
"""
Тест команд Telegram для системы резервирования
"""

import asyncio
import Config
from vinted_scanner import reservation_system, unified_reserve_command, reservation_status_command

class MockUpdate:
    """Мок объект для имитации Update"""
    def __init__(self, text="", args=None, reply_to_message=None):
        self.message = MockMessage(text, args, reply_to_message)

class MockMessage:
    """Мок объект для имитации Message"""
    def __init__(self, text, args=None, reply_to_message=None):
        self.text = text
        self.chat_id = -1002742804558  # Тестовый chat_id
        self.reply_to_message = reply_to_message
    
    async def reply_text(self, text, parse_mode=None):
        """Мок метод для reply_text"""
        print(f"  📤 Отправлено сообщение: {text[:50]}...")
        return True

class MockContext:
    """Мок объект для имитации Context"""
    def __init__(self, args=None):
        self.args = args or []

async def test_reserve_command():
    """Тест команды резервирования"""
    print("🧪 Тест команды /reserve")
    print("=" * 40)
    
    # Тест 1: Резервирование по ссылке
    print("\n📋 Тест 1: Резервирование по ссылке")
    update = MockUpdate("/reserve", ["https://www.vinted.de/items/test-item-123"])
    context = MockContext(["https://www.vinted.de/items/test-item-123"])
    
    try:
        await unified_reserve_command(update, context)
        print("  ✅ Команда выполнена успешно")
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 2: Резервирование по reply
    print("\n📋 Тест 2: Резервирование по reply")
    reply_message = MockMessage("Вот товар: https://www.vinted.de/items/test-item-456")
    update = MockUpdate("/reserve", reply_to_message=reply_message)
    context = MockContext()
    
    try:
        await unified_reserve_command(update, context)
        print("  ✅ Команда выполнена успешно")
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 3: Неверная ссылка
    print("\n📋 Тест 3: Неверная ссылка")
    update = MockUpdate("/reserve", ["https://example.com/wrong-link"])
    context = MockContext(["https://example.com/wrong-link"])
    
    try:
        await unified_reserve_command(update, context)
        print("  ✅ Команда выполнена успешно")
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)[:50]}")

async def test_reservations_command():
    """Тест команды статуса резервирований"""
    print("\n🧪 Тест команды /reservations")
    print("=" * 40)
    
    # Добавляем тестовые резервирования
    test_items = [
        {
            "url": f"{Config.vinted_url}/items/test-item-1",
            "title": "Тестовый товар 1"
        },
        {
            "url": f"{Config.vinted_url}/items/test-item-2",
            "title": "Тестовый товар 2"
        }
    ]
    
    for item in test_items:
        item_id = item["url"].split('/')[-1]
        reservation_system.reserved_items[item_id] = {
            "url": item["url"],
            "title": item["title"],
            "reserved_at": asyncio.get_event_loop().time(),
            "paypal_url": f"{Config.vinted_url}/checkout/{item_id}/paypal"
        }
    
    update = MockUpdate("/reservations")
    context = MockContext()
    
    try:
        await reservation_status_command(update, context)
        print("  ✅ Команда выполнена успешно")
    except Exception as e:
        print(f"  ❌ Ошибка: {str(e)[:50]}")

async def test_reservation_system():
    """Полный тест системы резервирования"""
    print("🚀 Полный тест системы резервирования")
    print("=" * 50)
    
    # Проверяем конфигурацию
    print(f"\n📋 Конфигурация:")
    print(f"  Резервирование включено: {Config.reservation_enabled}")
    print(f"  Таймаут: {Config.reservation_timeout} сек")
    print(f"  Максимум товаров: {Config.reservation_max_items}")
    
    # Тестируем команды
    await test_reserve_command()
    await test_reservations_command()
    
    # Проверяем статус системы
    print(f"\n📊 Статус системы:")
    print(f"  Активных резервирований: {len(reservation_system.reserved_items)}")
    print(f"  Система инициализирована: {reservation_system is not None}")
    
    print(f"\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_reservation_system()) 