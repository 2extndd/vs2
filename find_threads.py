#!/usr/bin/env python3
import requests
import Config
import time

def find_working_thread_ids():
    """Автоматически находит рабочие thread_id для топиков"""
    url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
    
    print("🔍 Автоматический поиск рабочих thread_id...")
    print(f"📱 Chat ID: {Config.telegram_chat_id}")
    print(f"🤖 Bot Token: {Config.telegram_bot_token[:20]}...")
    print()
    
    working_threads = []
    
    # Тестируем диапазон от 1 до 50
    for test_id in range(1, 51):
        params = {
            "chat_id": Config.telegram_chat_id,
            "text": f"🧪 Тест thread_id {test_id}",
            "message_thread_id": test_id
        }
        
        try:
            response = requests.post(url, data=params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Thread {test_id} РАБОТАЕТ!")
                working_threads.append(test_id)
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_desc = error_data.get('description', 'Unknown error')
                print(f"❌ Thread {test_id}: {error_desc}")
                
        except Exception as e:
            print(f"❌ Thread {test_id}: Exception - {e}")
        
        # Небольшая задержка чтобы не получить rate limit
        time.sleep(0.3)
    
    print()
    print("📊 РЕЗУЛЬТАТЫ:")
    if working_threads:
        print(f"✅ Найдены рабочие thread_id: {working_threads}")
        print()
        print("🔧 Для обновления Config.py используйте эти thread_id:")
        
        # Распределим найденные thread_id по топикам
        topic_names = list(Config.topics.keys())
        for i, (topic_name, thread_id) in enumerate(zip(topic_names, working_threads)):
            print(f"'{topic_name}': {{'thread_id': {thread_id}, ...}}")
            if i >= len(working_threads) - 1:  # Если thread_id кончились
                break
        
        # Если топиков больше чем найденных thread_id
        if len(topic_names) > len(working_threads):
            print(f"\n⚠️ Найдено только {len(working_threads)} рабочих thread_id, но у вас {len(topic_names)} топиков.")
            print("Возможно, нужно создать больше топиков в Telegram или использовать один thread_id для нескольких топиков.")
        
    else:
        print("❌ Не найдено ни одного рабочего thread_id!")
        print("Возможные причины:")
        print("1. Чат не настроен как форум")
        print("2. Бот не имеет прав на отправку сообщений в топики")
        print("3. Топики не созданы в группе")

if __name__ == "__main__":
    find_working_thread_ids()
