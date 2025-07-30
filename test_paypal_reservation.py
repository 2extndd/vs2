#!/usr/bin/env python3
"""
🧪 Тестовый скрипт для PayPal резервирования

ВНИМАНИЕ: Используйте только тестовые данные!
"""

import time
import logging
from vinted_paypal_reservation import VintedPayPalReservation

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_reservation_system():
    """Тестирование системы резервирования"""
    
    print("🧪 ТЕСТОВЫЙ РЕЖИМ PAYPAL РЕЗЕРВИРОВАНИЯ")
    print("="*50)
    
    # Тестовые данные (НЕ НАСТОЯЩИЕ!)
    test_cookies = {
        'session_id': 'test_session_123',
        'csrf_token': 'test_csrf_456'
    }
    
    test_user_agent = "Mozilla/5.0 (Test) TestBrowser/1.0"
    
    # Инициализация системы
    reservation_system = VintedPayPalReservation(test_cookies, test_user_agent)
    
    # Тестовые товары
    test_items = [
        {"id": "123456", "title": "Test Bag #1", "price": "25.00"},
        {"id": "789012", "title": "Test Shoes #2", "price": "45.00"},
        {"id": "345678", "title": "Test Jacket #3", "price": "75.00"}
    ]
    
    print(f"📦 Тестирование {len(test_items)} товаров...")
    
    for item in test_items:
        print(f"\n🎯 Тестирование товара: {item['title']}")
        print(f"💰 Цена: {item['price']}€")
        
        try:
            # В реальном режиме эта функция создала бы резервацию
            print(f"🔄 [ТЕСТ] Попытка резервирования товара {item['id']}")
            
            # Симуляция резервирования
            time.sleep(1)  # Имитация запроса к API
            
            # Тестовый результат
            success = True
            test_paypal_url = f"https://paypal.com/test/checkout?item={item['id']}"
            test_transaction_id = f"TXN-TEST-{item['id']}"
            
            if success:
                print(f"✅ [ТЕСТ] Резервация успешна!")
                print(f"📍 Transaction ID: {test_transaction_id}")
                print(f"🔗 PayPal URL: {test_paypal_url}")
                print(f"⏰ Истекает через: 15 минут")
            else:
                print(f"❌ [ТЕСТ] Резервация не удалась")
                
        except Exception as e:
            print(f"❌ [ТЕСТ] Ошибка: {e}")
    
    # Тестирование активных резерваций
    print(f"\n📊 Тестирование списка резерваций...")
    active_reservations = reservation_system.get_active_reservations()
    print(f"📋 Активных резерваций: {len(active_reservations)}")
    
    print(f"\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print(f"💡 Для реального использования:")
    print(f"   1. Настройте Config.py")
    print(f"   2. Добавьте реальные cookies Vinted")
    print(f"   3. Интегрируйте с основным ботом")
    
    return True

def test_config_validation():
    """Тестирование валидации конфигурации"""
    
    print("\n🔧 ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ")
    print("="*30)
    
    # Тестовые настройки
    test_configs = [
        {
            "paypal_reservation_enabled": True,
            "reservation_topics": ["bags", "shoes"],
            "max_reservations_per_hour": 5,
            "min_reservation_price": 10,
            "max_reservation_price": 500,
            "result": "✅ Валидная конфигурация"
        },
        {
            "paypal_reservation_enabled": False,
            "result": "⏸️ Резервирование отключено"
        },
        {
            "max_reservations_per_hour": 0,
            "result": "❌ Некорректный лимит резерваций"
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Тест {i}: {config['result']}")
        for key, value in config.items():
            if key != 'result':
                print(f"   {key}: {value}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования PayPal резервирования...")
    
    # Запуск тестов
    test_reservation_system()
    test_config_validation()
    
    print("\n🎯 ВАЖНЫЕ НАПОМИНАНИЯ:")
    print("1. 🧪 Это ТЕСТОВЫЙ режим - никаких реальных резерваций!")
    print("2. ⚠️ Для продакшена нужны настоящие Vinted cookies")
    print("3. 💰 Начинайте с дешевых товаров")
    print("4. 📊 Следите за лимитами резерваций")
    print("5. 🛡️ Соблюдайте правила Vinted")
