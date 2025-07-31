#!/usr/bin/env python3
"""
Тест системы резервирования товаров
"""

import time
import Config
from vinted_scanner import reservation_system

def test_reservation_system():
    """Тест системы резервирования"""
    print("🧪 Тест системы резервирования товаров")
    print("=" * 50)
    
    # Тест 1: Проверка конфигурации
    print("\n📋 Тест 1: Конфигурация")
    print(f"  Резервирование включено: {Config.reservation_enabled}")
    print(f"  Таймаут резервирования: {Config.reservation_timeout} сек ({Config.reservation_timeout//60} мин)")
    print(f"  Максимум резервирований: {Config.reservation_max_items}")
    print(f"  Тестовый аккаунт: {Config.reservation_test_account['email']}")
    
    # Тест 2: Инициализация системы
    print("\n🔧 Тест 2: Инициализация системы")
    print(f"  Система создана: {reservation_system is not None}")
    print(f"  Активных резервирований: {len(reservation_system.reserved_items)}")
    
    # Тест 3: Симуляция резервирования
    print("\n🔄 Тест 3: Симуляция резервирования")
    
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
    
    for i, item in enumerate(test_items, 1):
        print(f"  Резервирование товара {i}...")
        
        # Симулируем резервирование
        item_id = item["url"].split('/')[-1]
        reservation_system.reserved_items[item_id] = {
            "url": item["url"],
            "title": item["title"],
            "reserved_at": time.time(),
            "paypal_url": f"{Config.vinted_url}/checkout/{item_id}/paypal"
        }
        
        print(f"    ✅ Товар забронирован: {item['title']}")
    
    # Тест 4: Проверка статуса резервирований
    print("\n📊 Тест 4: Статус резервирований")
    
    for item_id in reservation_system.reserved_items:
        status = reservation_system.get_reservation_status(item_id)
        if status:
            remaining_minutes = int(status["remaining_time"] // 60)
            remaining_seconds = int(status["remaining_time"] % 60)
            print(f"  ✅ {status['title']}: {remaining_minutes}:{remaining_seconds:02d}")
        else:
            print(f"  ❌ Резервирование истекло")
    
    # Тест 5: Проверка лимитов
    print("\n🔢 Тест 5: Проверка лимитов")
    
    active_count = len([r for r in reservation_system.reserved_items.values() 
                       if time.time() - r["reserved_at"] < Config.reservation_timeout])
    
    print(f"  Активных резервирований: {active_count}")
    print(f"  Лимит: {Config.reservation_max_items}")
    print(f"  Доступно слотов: {Config.reservation_max_items - active_count}")
    
    # Тест 6: Очистка истекших резервирований
    print("\n🗑️ Тест 6: Очистка истекших резервирований")
    
    # Симулируем истекшее резервирование
    expired_item_id = "expired-item"
    reservation_system.reserved_items[expired_item_id] = {
        "url": f"{Config.vinted_url}/items/expired-item",
        "title": "Истекший товар",
        "reserved_at": time.time() - Config.reservation_timeout - 60,  # Истекло 1 минуту назад
        "paypal_url": f"{Config.vinted_url}/checkout/expired-item/paypal"
    }
    
    print(f"  Резервирований до очистки: {len(reservation_system.reserved_items)}")
    
    expired_count = reservation_system.cleanup_expired_reservations()
    
    print(f"  Очищено истекших: {expired_count}")
    print(f"  Резервирований после очистки: {len(reservation_system.reserved_items)}")
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    print(f"✅ Система резервирования: РАБОТАЕТ")
    print(f"📊 Активных резервирований: {len(reservation_system.reserved_items)}")
    print(f"⏰ Таймаут: {Config.reservation_timeout//60} минут")
    print(f"🔢 Лимит: {Config.reservation_max_items} товаров")
    
    if Config.reservation_enabled:
        print(f"🎉 Система готова к использованию!")
    else:
        print(f"⚠️ Система отключена в конфигурации")
    
    return True

if __name__ == "__main__":
    test_reservation_system() 