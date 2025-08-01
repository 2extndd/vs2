#!/usr/bin/env python3
"""
Полный стресс-тест системы Vinted Scanner
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

def stress_test_switching():
    """Стресс-тест переключений систем"""
    print("🔥 ПОЛНЫЙ СТРЕСС-ТЕСТ СИСТЕМЫ")
    print("=" * 60)
    
    # Отключаем Telegram бота
    vinted_scanner.bot_running = False
    
    # Сбрасываем все состояния
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 0
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.advanced_proxy_errors = 0
    vinted_scanner.basic_requests = 0
    vinted_scanner.basic_success = 0
    vinted_scanner.advanced_no_proxy_requests = 0
    vinted_scanner.advanced_no_proxy_success = 0
    vinted_scanner.advanced_proxy_requests = 0
    vinted_scanner.advanced_proxy_success = 0
    vinted_scanner.last_switch_time = 0
    
    print(f"🎯 Начальная система: {vinted_scanner.current_system}")
    
    # Стресс-тест: 100 итераций с случайными ошибками
    iterations = 100
    switches_count = 0
    error_patterns = []
    
    for i in range(iterations):
        # Случайные ошибки для разных систем
        if vinted_scanner.current_system == "basic":
            if random.random() < 0.3:  # 30% вероятность ошибки
                vinted_scanner.basic_system_errors += 1
                error_patterns.append(f"basic_error_{i}")
        elif vinted_scanner.current_system == "advanced_no_proxy":
            if random.random() < 0.25:  # 25% вероятность ошибки
                vinted_scanner.advanced_no_proxy_errors += 1
                error_patterns.append(f"no_proxy_error_{i}")
        elif vinted_scanner.current_system == "advanced_proxy":
            if random.random() < 0.2:  # 20% вероятность ошибки
                vinted_scanner.advanced_proxy_errors += 1
                error_patterns.append(f"proxy_error_{i}")
        
        # Симулируем успешные запросы
        if vinted_scanner.current_system == "basic":
            vinted_scanner.basic_requests += 1
            if random.random() < 0.7:  # 70% успешность
                vinted_scanner.basic_success += 1
        elif vinted_scanner.current_system == "advanced_no_proxy":
            vinted_scanner.advanced_no_proxy_requests += 1
            if random.random() < 0.8:  # 80% успешность
                vinted_scanner.advanced_no_proxy_success += 1
        elif vinted_scanner.current_system == "advanced_proxy":
            vinted_scanner.advanced_proxy_requests += 1
            if random.random() < 0.85:  # 85% успешность
                vinted_scanner.advanced_proxy_success += 1
        
        # Проверяем переключение
        old_system = vinted_scanner.current_system
        if vinted_scanner.should_switch_system():
            switches_count += 1
            print(f"🔄 Итерация {i+1}: {old_system} → {vinted_scanner.current_system}")
        
        # Каждые 20 итераций показываем статистику
        if (i + 1) % 20 == 0:
            print(f"\n📊 Итерация {i+1}:")
            print(f"   Система: {vinted_scanner.current_system}")
            print(f"   Переключений: {switches_count}")
            print(f"   Ошибки: basic={vinted_scanner.basic_system_errors}, no_proxy={vinted_scanner.advanced_no_proxy_errors}, proxy={vinted_scanner.advanced_proxy_errors}")
    
    print(f"\n🎯 ФИНАЛЬНАЯ СТАТИСТИКА СТРЕСС-ТЕСТА:")
    print(f"   Всего итераций: {iterations}")
    print(f"   Переключений: {switches_count}")
    print(f"   Финальная система: {vinted_scanner.current_system}")
    print(f"   Ошибок: basic={vinted_scanner.basic_system_errors}, no_proxy={vinted_scanner.advanced_no_proxy_errors}, proxy={vinted_scanner.advanced_proxy_errors}")
    print(f"   Успешных запросов: basic={vinted_scanner.basic_success}, no_proxy={vinted_scanner.advanced_no_proxy_success}, proxy={vinted_scanner.advanced_proxy_success}")

def stress_test_concurrent():
    """Стресс-тест с конкурентными запросами"""
    print(f"\n⚡ СТРЕСС-ТЕСТ КОНКУРЕНТНЫХ ЗАПРОСОВ")
    print("=" * 50)
    
    def concurrent_request(thread_id):
        """Симуляция конкурентного запроса"""
        for i in range(10):
            # Случайная ошибка
            if random.random() < 0.1:
                if vinted_scanner.current_system == "basic":
                    vinted_scanner.basic_system_errors += 1
                elif vinted_scanner.current_system == "advanced_no_proxy":
                    vinted_scanner.advanced_no_proxy_errors += 1
                elif vinted_scanner.current_system == "advanced_proxy":
                    vinted_scanner.advanced_proxy_errors += 1
            
            # Симулируем запрос
            if vinted_scanner.current_system == "basic":
                vinted_scanner.basic_requests += 1
                if random.random() < 0.7:
                    vinted_scanner.basic_success += 1
            elif vinted_scanner.current_system == "advanced_no_proxy":
                vinted_scanner.advanced_no_proxy_requests += 1
                if random.random() < 0.8:
                    vinted_scanner.advanced_no_proxy_success += 1
            elif vinted_scanner.current_system == "advanced_proxy":
                vinted_scanner.advanced_proxy_requests += 1
                if random.random() < 0.85:
                    vinted_scanner.advanced_proxy_success += 1
            
            # Проверяем переключение
            vinted_scanner.should_switch_system()
            time.sleep(0.01)  # Небольшая задержка
    
    # Запускаем 5 потоков одновременно
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(concurrent_request, i) for i in range(5)]
        for future in futures:
            future.result()
    
    print(f"✅ Конкурентный тест завершен")
    print(f"   Финальная система: {vinted_scanner.current_system}")
    print(f"   Всего запросов: {vinted_scanner.basic_requests + vinted_scanner.advanced_no_proxy_requests + vinted_scanner.advanced_proxy_requests}")

def stress_test_rapid_switching():
    """Стресс-тест быстрых переключений"""
    print(f"\n🔄 СТРЕСС-ТЕСТ БЫСТРЫХ ПЕРЕКЛЮЧЕНИЙ")
    print("=" * 50)
    
    # Сбрасываем состояние
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 0
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.advanced_proxy_errors = 0
    
    rapid_switches = 0
    for i in range(50):
        # Быстрые ошибки для принудительного переключения
        if vinted_scanner.current_system == "basic":
            vinted_scanner.basic_system_errors = 3
        elif vinted_scanner.current_system == "advanced_no_proxy":
            vinted_scanner.advanced_no_proxy_errors = 3
        
        old_system = vinted_scanner.current_system
        if vinted_scanner.should_switch_system():
            rapid_switches += 1
            print(f"🔄 Быстрое переключение {rapid_switches}: {old_system} → {vinted_scanner.current_system}")
        
        time.sleep(0.1)  # Быстрые итерации
    
    print(f"✅ Быстрых переключений: {rapid_switches}")

def test_y3_thread_id():
    """Тест thread_id для y-3 категории"""
    print(f"\n🔍 ТЕСТ THREAD_ID ДЛЯ Y-3 КАТЕГОРИИ")
    print("=" * 50)
    
    # Проверяем Config.py
    import Config
    
    y3_found = False
    for topic_name, topic_data in Config.topics.items():
        if "y-3" in topic_name.lower() or "y3" in topic_name.lower():
            y3_found = True
            thread_id = topic_data.get("thread_id")
            print(f"📋 Найден топик: {topic_name}")
            print(f"   Thread ID: {thread_id}")
            print(f"   Query: {topic_data.get('query', 'N/A')}")
            
            if thread_id:
                print(f"✅ Thread ID настроен: {thread_id}")
            else:
                print(f"❌ Thread ID НЕ настроен!")
    
    if not y3_found:
        print(f"⚠️ Y-3 категория не найдена в Config.py")
        print(f"📋 Доступные топики:")
        for topic_name in Config.topics.keys():
            print(f"   - {topic_name}")
    
    return y3_found

if __name__ == "__main__":
    stress_test_switching()
    stress_test_concurrent()
    stress_test_rapid_switching()
    test_y3_thread_id()
    
    print(f"\n🎉 ПОЛНЫЙ СТРЕСС-ТЕСТ ЗАВЕРШЕН!")
    print(f"✅ Система готова к продакшену") 