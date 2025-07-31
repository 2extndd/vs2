#!/usr/bin/env python3
"""
Тест команды /status
"""

import logging
import Config
from advanced_antiban import advanced_system

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_status_command():
    """Тест команды /status"""
    print("🧪 ТЕСТ КОМАНДЫ /STATUS:")
    print("=" * 40)
    
    # Симулируем команду /status
    if True:  # ADVANCED_SYSTEM_AVAILABLE
        stats = advanced_system.get_stats()
        print(f"🚀 Продвинутая система:")
        print(f"   📊 HTTP: {stats['http_success']}/{stats['http_requests']}")
        print(f"   🌐 Browser: {stats['browser_success']}/{stats['browser_requests']}")
        print(f"   📈 Успешность: {stats['success_rate']:.1f}%")
        print(f"   ⚠️ Ошибок подряд: 0/5")
        print(f"   🔄 Режим: auto")
    
    # Делаем несколько запросов
    print("\n🚀 Делаем несколько запросов...")
    url = f"{Config.vinted_url}/api/v2/catalog/items"
    params = {'page': '1', 'per_page': '2'}
    
    for i in range(3):
        print(f"📊 Запрос {i+1}...")
        result = advanced_system.make_http_request(url, params)
        print(f"   Результат: {result is not None}")
        
        # Проверяем статистику после каждого запроса
        stats = advanced_system.get_stats()
        print(f"   Статистика: HTTP={stats['http_success']}/{stats['http_requests']}")
    
    # Финальная статистика
    print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    stats = advanced_system.get_stats()
    print(f"🚀 Продвинутая система:")
    print(f"   📊 HTTP: {stats['http_success']}/{stats['http_requests']}")
    print(f"   🌐 Browser: {stats['browser_success']}/{stats['browser_requests']}")
    print(f"   📈 Успешность: {stats['success_rate']:.1f}%")

if __name__ == "__main__":
    test_status_command() 