#!/usr/bin/env python3
import requests
import Config
import json

def check_chat_info():
    """Проверяет информацию о чате"""
    url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/getChat"
    params = {"chat_id": Config.telegram_chat_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            chat = data['result']
            
            print("📊 Информация о чате:")
            print(f"• ID: {chat.get('id')}")
            print(f"• Тип: {chat.get('type')}")
            print(f"• Название: {chat.get('title', 'Без названия')}")
            print(f"• Описание: {chat.get('description', 'Нет')}")
            print(f"• Форум: {chat.get('is_forum', False)}")
            
            if not chat.get('is_forum', False):
                print("\n⚠️ ПРОБЛЕМА: Группа НЕ настроена как форум!")
                print("\n🔧 Что нужно сделать:")
                print("1. Зайдите в настройки вашей Telegram группы")
                print("2. Найдите опцию 'Topics' или 'Темы'")
                print("3. Включите эту опцию")
                print("4. Создайте нужные темы/топики")
                print("5. Запустите этот скрипт снова")
                
                # Временное решение - отключить топики
                print("\n🚨 ВРЕМЕННОЕ РЕШЕНИЕ:")
                print("Можно отключить использование топиков в Config.py")
                print("Установив thread_id: None для всех топиков")
                
            else:
                print("\n✅ Группа настроена как форум!")
                print("Возможно, нужно создать топики или проверить права бота")
        else:
            print(f"❌ Ошибка получения информации о чате: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

def test_main_chat():
    """Тестирует отправку в основной чат"""
    url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
    params = {
        "chat_id": Config.telegram_chat_id,
        "text": "🧪 Тест отправки в основной чат (без топиков)"
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ Отправка в основной чат работает!")
        else:
            print(f"❌ Ошибка отправки в основной чат: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")

if __name__ == "__main__":
    check_chat_info()
    print("\n" + "="*50 + "\n")
    test_main_chat()
