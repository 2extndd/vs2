#!/usr/bin/env python3
import re

def disable_all_topics():
    """Отключает топики для всех записей в Config.py"""
    
    with open('Config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем все "thread_id": любое_число на "thread_id": None
    updated_content = re.sub(r'"thread_id":\s*\d+', '"thread_id": None', content)
    
    with open('Config.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Все топики отключены (thread_id установлен в None)")
    print("📬 Все уведомления будут отправляться в основной чат")
    print("\n🔧 Когда создадите топики в Telegram:")
    print("1. Создайте топики в вашей группе VintedSale")
    print("2. Запустите find_threads.py для поиска правильных thread_id")
    print("3. Обновите Config.py с найденными thread_id")

if __name__ == "__main__":
    disable_all_topics()
