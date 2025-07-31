#!/usr/bin/env python3
"""
Тест скорости антибан системы для продакшена
"""

import time
import requests
from antiban_fast import fast_antiban_system

def production_speed_test():
    """Тест скорости для продакшена"""
    print("🚀 ТЕСТ СКОРОСТИ ДЛЯ ПРОДАКШЕНА")
    print("=" * 50)
    
    # Тест базовых запросов
    test_params = {
        'page': '1',
        'per_page': '2',
        'order': 'newest_first'
    }
    
    print("\n⚡ Тест скорости (10 запросов):")
    
    start_time = time.time()
    success_count = 0
    
    for i in range(10):
        try:
            result = fast_antiban_system.smart_request(
                "https://httpbin.org/json",  # Тестовый эндпоинт
                test_params
            )
            if result[1]:  # success
                success_count += 1
                print(f"  ✅ Запрос {i+1}: успех")
            else:
                print(f"  ❌ Запрос {i+1}: провал")
        except Exception as e:
            print(f"  ❌ Запрос {i+1}: ошибка")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    stats = fast_antiban_system.get_stats()
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА СКОРОСТИ:")
    print(f"  Время: {total_time:.2f} сек")
    print(f"  Скорость: {10/total_time:.2f} запросов/сек")
    print(f"  Успешных: {success_count}/10")
    print(f"  Процент успеха: {stats['success_rate']:.1f}%")
    
    # Оценка готовности
    if total_time < 15 and success_count >= 8:
        print(f"\n🎉 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        print(f"  Быстрая работа: {10/total_time:.1f} запросов/сек")
        print(f"  Высокая надежность: {success_count}/10 успешных")
        return True
    else:
        print(f"\n⚠️ ТРЕБУЕТСЯ ОПТИМИЗАЦИЯ")
        if total_time >= 15:
            print(f"  Слишком медленно: {total_time:.1f}s (нужно <15s)")
        if success_count < 8:
            print(f"  Низкая надежность: {success_count}/10 (нужно >=8)")
        return False

if __name__ == "__main__":
    production_speed_test()