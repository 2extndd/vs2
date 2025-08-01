#!/usr/bin/env python3
"""
Тест проблемы с y-3 категорией
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Config
import vinted_scanner

def test_y3_configuration():
    """Проверяем конфигурацию y-3 категории"""
    print("🔍 ДИАГНОСТИКА Y-3 КАТЕГОРИИ")
    print("=" * 50)
    
    y3_topics = []
    
    # Ищем все топики, связанные с y-3
    for topic_name, topic_data in Config.topics.items():
        if "y-3" in topic_name.lower() or "y3" in topic_name.lower() or "yohji" in topic_name.lower():
            y3_topics.append({
                "name": topic_name,
                "data": topic_data,
                "thread_id": topic_data.get("thread_id"),
                "query": topic_data.get("query", "N/A")
            })
    
    if not y3_topics:
        print("❌ Y-3 категории не найдены в Config.py")
        print("\n📋 Доступные топики:")
        for topic_name in Config.topics.keys():
            print(f"   - {topic_name}")
        return False
    
    print(f"✅ Найдено {len(y3_topics)} Y-3 категорий:")
    
    for i, topic in enumerate(y3_topics, 1):
        print(f"\n📋 Y-3 категория {i}: {topic['name']}")
        print(f"   Thread ID: {topic['thread_id']}")
        print(f"   Query: {topic['query']}")
        
        if topic['thread_id']:
            print(f"   ✅ Thread ID настроен: {topic['thread_id']}")
        else:
            print(f"   ❌ Thread ID НЕ настроен!")
    
    return True

def test_y3_sending_logic():
    """Тестируем логику отправки для y-3"""
    print(f"\n📤 ТЕСТ ЛОГИКИ ОТПРАВКИ Y-3")
    print("-" * 40)
    
    # Симулируем отправку сообщения для y-3 категории
    y3_topics = []
    for topic_name, topic_data in Config.topics.items():
        if "y-3" in topic_name.lower() or "y3" in topic_name.lower() or "yohji" in topic_name.lower():
            y3_topics.append({
                "name": topic_name,
                "thread_id": topic_data.get("thread_id"),
                "query": topic_data.get("query", "N/A")
            })
    
    for topic in y3_topics:
        print(f"\n📋 Тестируем отправку для: {topic['name']}")
        
        if topic['thread_id']:
            print(f"   🎯 Thread ID: {topic['thread_id']}")
            print(f"   📤 Должно отправляться в топик")
            
            # Симулируем вызов send_telegram_message
            thread_id = topic['thread_id']
            topic_info = f"Y-3: {topic['name']}"
            
            print(f"   ✅ Параметры корректны:")
            print(f"      - thread_id: {thread_id}")
            print(f"      - topic_info: {topic_info}")
        else:
            print(f"   ❌ Thread ID не настроен!")
            print(f"   📱 Будет отправляться в main chat")
    
    return len(y3_topics) > 0

def test_y3_telegram_api():
    """Тестируем доступность Y-3 топиков через Telegram API"""
    print(f"\n🤖 ТЕСТ TELEGRAM API ДЛЯ Y-3")
    print("-" * 40)
    
    import requests
    
    y3_topics = []
    for topic_name, topic_data in Config.topics.items():
        if "y-3" in topic_name.lower() or "y3" in topic_name.lower() or "yohji" in topic_name.lower():
            thread_id = topic_data.get("thread_id")
            if thread_id:
                y3_topics.append({
                    "name": topic_name,
                    "thread_id": thread_id
                })
    
    if not y3_topics:
        print("❌ Нет Y-3 топиков с настроенным thread_id")
        return False
    
    print(f"🔍 Тестируем {len(y3_topics)} Y-3 топиков:")
    
    for topic in y3_topics:
        print(f"\n📋 Топик: {topic['name']}")
        print(f"   Thread ID: {topic['thread_id']}")
        
        # Тестируем отправку тестового сообщения
        try:
            test_message = f"🧪 Тест Y-3 топика: {topic['name']}"
            
            response = requests.post(
                f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage",
                data={
                    "chat_id": Config.telegram_chat_id,
                    "message_thread_id": topic['thread_id'],
                    "text": test_message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Топик доступен")
            elif response.status_code == 400:
                print(f"   ❌ Топик недоступен (400 Bad Request)")
                print(f"   📱 Сообщения будут отправляться в main chat")
            else:
                print(f"   ⚠️ Неожиданный ответ: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка API: {str(e)[:50]}")
    
    return True

def suggest_y3_fixes():
    """Предлагаем исправления для Y-3"""
    print(f"\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ Y-3")
    print("-" * 40)
    
    y3_topics = []
    for topic_name, topic_data in Config.topics.items():
        if "y-3" in topic_name.lower() or "y3" in topic_name.lower() or "yohji" in topic_name.lower():
            thread_id = topic_data.get("thread_id")
            y3_topics.append({
                "name": topic_name,
                "thread_id": thread_id,
                "has_thread_id": bool(thread_id)
            })
    
    if not y3_topics:
        print("❌ Y-3 категории не найдены")
        return
    
    print("📋 Статус Y-3 категорий:")
    for topic in y3_topics:
        status = "✅" if topic['has_thread_id'] else "❌"
        print(f"   {status} {topic['name']}: {topic['thread_id'] or 'НЕТ'}")
    
    # Проверяем, есть ли категории без thread_id
    missing_thread_id = [t for t in y3_topics if not t['has_thread_id']]
    
    if missing_thread_id:
        print(f"\n⚠️ ПРОБЛЕМА: {len(missing_thread_id)} Y-3 категорий без thread_id:")
        for topic in missing_thread_id:
            print(f"   - {topic['name']}")
        
        print(f"\n🔧 РЕШЕНИЕ:")
        print(f"   1. Добавить thread_id для этих категорий в Config.py")
        print(f"   2. Или создать новые топики в Telegram")
        print(f"   3. Или временно отключить эти категории")
    else:
        print(f"\n✅ Все Y-3 категории имеют thread_id")
        print(f"   Проверьте доступность топиков через Telegram API")

if __name__ == "__main__":
    test_y3_configuration()
    test_y3_sending_logic()
    test_y3_telegram_api()
    suggest_y3_fixes()
    
    print(f"\n🎯 ДИАГНОСТИКА Y-3 ЗАВЕРШЕНА!") 