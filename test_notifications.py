#!/usr/bin/env python3
"""
Тест уведомлений (Telegram, Email, Slack)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import Config
from vinted_scanner import (
    send_telegram_message, send_email, send_slack_message
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_telegram_notification():
    """Тест Telegram уведомлений"""
    print("\n📱 ТЕСТ TELEGRAM УВЕДОМЛЕНИЙ:")
    print("=" * 40)
    
    if not Config.telegram_bot_token or not Config.telegram_chat_id:
        print("❌ Telegram не настроен")
        return False
    
    # Тестовые данные
    test_item = {
        'title': '🧪 ТЕСТОВЫЙ ТОВАР',
        'price': '25.0 EUR',
        'url': 'https://www.vinted.de/items/test',
        'image': 'https://via.placeholder.com/300x400',
        'size': 'M'
    }
    
    try:
        print("📤 Отправляем тестовое уведомление...")
        success = send_telegram_message(
            test_item['title'],
            test_item['price'],
            test_item['url'],
            test_item['image'],
            test_item['size'],
            thread_id=190
        )
        
        if success:
            print("✅ Telegram уведомление отправлено успешно")
            return True
        else:
            print("❌ Ошибка отправки Telegram уведомления")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_email_notification():
    """Тест Email уведомлений"""
    print("\n📧 ТЕСТ EMAIL УВЕДОМЛЕНИЙ:")
    print("=" * 35)
    
    if not Config.smtp_username or not Config.smtp_server:
        print("❌ Email не настроен")
        return False
    
    # Тестовые данные
    test_item = {
        'title': '🧪 ТЕСТОВЫЙ ТОВАР',
        'price': '25.0 EUR',
        'url': 'https://www.vinted.de/items/test',
        'image': 'https://via.placeholder.com/300x400',
        'size': 'M'
    }
    
    try:
        print("📤 Отправляем тестовое email...")
        send_email(
            test_item['title'],
            test_item['price'],
            test_item['url'],
            test_item['image'],
            test_item['size']
        )
        print("✅ Email уведомление отправлено успешно")
        return True
        
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_slack_notification():
    """Тест Slack уведомлений"""
    print("\n💬 ТЕСТ SLACK УВЕДОМЛЕНИЙ:")
    print("=" * 35)
    
    if not Config.slack_webhook_url:
        print("❌ Slack не настроен")
        return False
    
    # Тестовые данные
    test_item = {
        'title': '🧪 ТЕСТОВЫЙ ТОВАР',
        'price': '25.0 EUR',
        'url': 'https://www.vinted.de/items/test',
        'image': 'https://via.placeholder.com/300x400',
        'size': 'M'
    }
    
    try:
        print("📤 Отправляем тестовое Slack уведомление...")
        send_slack_message(
            test_item['title'],
            test_item['price'],
            test_item['url'],
            test_item['image'],
            test_item['size']
        )
        print("✅ Slack уведомление отправлено успешно")
        return True
        
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_config_validation():
    """Тест валидации конфигурации"""
    print("\n⚙️ ТЕСТ ВАЛИДАЦИИ КОНФИГУРАЦИИ:")
    print("=" * 45)
    
    config_checks = {
        'Vinted URL': bool(Config.vinted_url),
        'Telegram Bot Token': bool(Config.telegram_bot_token),
        'Telegram Chat ID': bool(Config.telegram_chat_id),
        'SMTP Username': bool(Config.smtp_username),
        'SMTP Server': bool(Config.smtp_server),
        'Slack Webhook': bool(Config.slack_webhook_url),
        'Topics Count': len(Config.topics) > 0
    }
    
    print("📋 Проверка настроек:")
    for setting, is_set in config_checks.items():
        status = "✅" if is_set else "❌"
        print(f"   {status} {setting}")
    
    passed = sum(config_checks.values())
    total = len(config_checks)
    
    print(f"\n📊 Результат: {passed}/{total} настроек корректны")
    
    if passed == total:
        print("🎉 Все настройки корректны!")
        return True
    else:
        print("⚠️ Некоторые настройки отсутствуют")
        return False

def test_real_item_processing():
    """Тест обработки реального товара"""
    print("\n🛍️ ТЕСТ ОБРАБОТКИ РЕАЛЬНОГО ТОВАРА:")
    print("=" * 45)
    
    # Симулируем реальный товар из Vinted
    real_item = {
        'id': '6787967420',
        'title': 'George Gina & Lucy Tasche',
        'price': {'amount': '18.0', 'currency_code': 'EUR'},
        'url': 'https://www.vinted.de/items/6787967420',
        'photo': {'full_size_url': 'https://img01-vinted-com.akamaized.net/...'},
        'size_title': 'M'
    }
    
    print(f"📦 Обрабатываем товар: {real_item['title']}")
    print(f"💰 Цена: {real_item['price']['amount']} {real_item['price']['currency_code']}")
    print(f"🔗 URL: {real_item['url']}")
    print(f"📏 Размер: {real_item.get('size_title', 'N/A')}")
    
    # Проверяем отправку уведомлений
    notifications_sent = 0
    
    # Telegram
    if Config.telegram_bot_token and Config.telegram_chat_id:
        try:
            success = send_telegram_message(
                real_item['title'],
                f"{real_item['price']['amount']} {real_item['price']['currency_code']}",
                real_item['url'],
                real_item['photo']['full_size_url'],
                real_item.get('size_title'),
                thread_id=190
            )
            if success:
                notifications_sent += 1
                print("✅ Telegram уведомление отправлено")
        except Exception as e:
            print(f"❌ Ошибка Telegram: {e}")
    
    # Email
    if Config.smtp_username and Config.smtp_server:
        try:
            send_email(
                real_item['title'],
                f"{real_item['price']['amount']} {real_item['price']['currency_code']}",
                real_item['url'],
                real_item['photo']['full_size_url'],
                real_item.get('size_title')
            )
            notifications_sent += 1
            print("✅ Email уведомление отправлено")
        except Exception as e:
            print(f"❌ Ошибка Email: {e}")
    
    # Slack
    if Config.slack_webhook_url:
        try:
            send_slack_message(
                real_item['title'],
                f"{real_item['price']['amount']} {real_item['price']['currency_code']}",
                real_item['url'],
                real_item['photo']['full_size_url'],
                real_item.get('size_title')
            )
            notifications_sent += 1
            print("✅ Slack уведомление отправлено")
        except Exception as e:
            print(f"❌ Ошибка Slack: {e}")
    
    print(f"\n📊 Отправлено уведомлений: {notifications_sent}")
    return notifications_sent > 0

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ УВЕДОМЛЕНИЙ")
    print("=" * 40)
    
    results = {
        'config_validation': False,
        'telegram_notification': False,
        'email_notification': False,
        'slack_notification': False,
        'real_item_processing': False
    }
    
    try:
        # Тест конфигурации
        results['config_validation'] = test_config_validation()
        
        # Тест Telegram
        results['telegram_notification'] = test_telegram_notification()
        
        # Тест Email
        results['email_notification'] = test_email_notification()
        
        # Тест Slack
        results['slack_notification'] = test_slack_notification()
        
        # Тест обработки реального товара
        results['real_item_processing'] = test_real_item_processing()
        
        # Итоговая статистика
        print("\n📊 ИТОГОВАЯ СТАТИСТИКА УВЕДОМЛЕНИЙ:")
        print("=" * 45)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test}: {status}")
        
        print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 ВСЕ УВЕДОМЛЕНИЯ РАБОТАЮТ!")
        else:
            print("⚠️ НЕКОТОРЫЕ УВЕДОМЛЕНИЯ НЕ РАБОТАЮТ")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 