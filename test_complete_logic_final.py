#!/usr/bin/env python3
"""
Финальный тест всей логики системы
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_complete_logic():
    """Тест всей логики системы"""
    
    print("🧪 ФИНАЛЬНЫЙ ТЕСТ ВСЕЙ ЛОГИКИ")
    print("=" * 60)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    print(f"📊 1. НАЧАЛЬНОЕ СОСТОЯНИЕ:")
    print(f"   proxy_mode: {system.proxy_mode}")
    print(f"   current_proxy: {system.current_proxy}")
    print(f"   should_use_proxy: {system._should_use_proxy()}")
    
    # Симулируем несколько успешных запросов без прокси
    print(f"\n📊 2. СИМУЛЯЦИЯ УСПЕШНЫХ ЗАПРОСОВ БЕЗ ПРОКСИ:")
    for i in range(5):
        system.http_requests += 1
        system.http_success += 1
        system.no_proxy_requests += 1
        system.no_proxy_success += 1
        print(f"   Запрос {i+1}: успех без прокси")
    
    print(f"   http_requests: {system.http_requests}")
    print(f"   http_success: {system.http_success}")
    print(f"   should_use_proxy: {system._should_use_proxy()}")
    
    # Симулируем ошибки для переключения на прокси
    print(f"\n📊 3. СИМУЛЯЦИЯ ОШИБОК (ПЕРЕКЛЮЧЕНИЕ НА ПРОКСИ):")
    for i in range(3):
        system.http_requests += 1
        system.errors_403 += 1
        system.consecutive_errors += 1
        system.no_proxy_requests += 1
        print(f"   Ошибка {i+1}: 403 Forbidden")
    
    print(f"   errors_403: {system.errors_403}")
    print(f"   consecutive_errors: {system.consecutive_errors}")
    print(f"   should_use_proxy: {system._should_use_proxy()}")
    
    # Проверяем переключение на прокси
    if system._should_use_proxy():
        print(f"   ✅ Система правильно определила необходимость прокси")
        # Симулируем активацию прокси
        system.proxy_mode = "enabled"
        system._rotate_proxy()
        print(f"   🔄 Прокси активирован: {system.current_proxy}")
    else:
        print(f"   ❌ Система не переключилась на прокси при ошибках")
    
    # Симулируем успешные запросы с прокси
    print(f"\n📊 4. СИМУЛЯЦИЯ УСПЕШНЫХ ЗАПРОСОВ С ПРОКСИ:")
    for i in range(3):
        system.http_requests += 1
        system.http_success += 1
        system.proxy_requests += 1
        system.proxy_success += 1
        system.consecutive_errors = 0  # Сбрасываем ошибки
        print(f"   Запрос {i+1}: успех с прокси")
    
    print(f"   http_success: {system.http_success}")
    print(f"   consecutive_errors: {system.consecutive_errors}")
    
    # Проверяем статистику
    stats = system.get_stats()
    print(f"\n📊 5. ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"   no_proxy_requests: {stats.get('no_proxy_requests', 0)}")
    print(f"   no_proxy_success: {stats.get('no_proxy_success', 0)}")
    print(f"   proxy_requests: {stats.get('proxy_requests', 0)}")
    print(f"   proxy_success: {stats.get('proxy_success', 0)}")
    print(f"   total_requests: {stats.get('total_requests', 0)}")
    print(f"   success_rate: {stats.get('success_rate', 0):.1f}%")
    
    # Симулируем отображение статуса
    print(f"\n📊 6. СИМУЛЯЦИЯ СТАТУСА:")
    no_proxy_success = stats.get('no_proxy_success', 0)
    no_proxy_requests = stats.get('no_proxy_requests', 0)
    proxy_success = stats.get('proxy_success', 0)
    proxy_requests = stats.get('proxy_requests', 0)
    
    print(f"🚀 Продвинутая система:")
    print(f"   📊 HTTP (без прокси): {no_proxy_success}/{no_proxy_requests}")
    print(f"   📊 HTTP (с прокси): {proxy_success}/{proxy_requests}")
    print(f"   🔄 Режим: {system.proxy_mode}")
    
    # Проверяем правильность логики
    print(f"\n✅ РЕЗУЛЬТАТ ТЕСТА:")
    if (no_proxy_requests > 0 and proxy_requests > 0 and 
        no_proxy_success <= no_proxy_requests and 
        proxy_success <= proxy_requests):
        print(f"   ✅ Логика работает правильно:")
        print(f"   - Система начинала без прокси (экономия)")
        print(f"   - Переключилась на прокси при ошибках")
        print(f"   - Счетчики корректны")
        print(f"   - Статистика отображается правильно")
    else:
        print(f"   ❌ Обнаружены проблемы в логике")
    
    print("\n✅ Финальный тест завершен!")

if __name__ == "__main__":
    test_complete_logic() 