#!/usr/bin/env python3
"""
Быстрый тест антибан системы
"""

import time
import random
from antiban_fast import fast_antiban_system

def quick_test():
    """Быстрый тест системы"""
    print("⚡ БЫСТРЫЙ ТЕСТ АНТИБАН СИСТЕМЫ")
    print("=" * 40)
    
    # Проверяем инициализацию
    print(f"\n🔧 Инициализация:")
    print(f"  Система создана: {'✅' if fast_antiban_system else '❌'}")
    
    # Быстрый тест запросов
    print(f"\n🔄 Быстрый тест (5 запросов):")
    
    test_params = {
        'page': '1',
        'per_page': '2',
        'search_text': 'test',
        'order': 'newest_first'
    }
    
    success_count = 0
    start_time = time.time()
    
    for i in range(5):
        print(f"  Запрос {i+1}/5...", end=" ")
        
        try:
            result = fast_antiban_system.get_vinted_items(test_params)
            if result:
                success_count += 1
                print("✅")
            else:
                print("❌")
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Статистика
    stats = fast_antiban_system.get_stats()
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"  Время: {total_time:.1f} сек")
    print(f"  Успешных: {success_count}/5")
    print(f"  Всего запросов: {stats['total_requests']}")
    print(f"  Всего ошибок: {stats['total_errors']}")
    print(f"  Блокировок: {stats['total_blocks']}")
    print(f"  Процент успеха: {stats['success_rate']:.1f}%")
    print(f"  Ротаций сессий: {stats['session_rotations']}")
    
    # Оценка
    if success_count >= 3:
        print(f"\n✅ СИСТЕМА РАБОТАЕТ!")
        print(f"  Скорость: {5/total_time:.2f} запросов/сек")
        return True
    else:
        print(f"\n❌ СИСТЕМА НУЖДАЕТСЯ В НАСТРОЙКЕ")
        return False

if __name__ == "__main__":
    quick_test()