#!/usr/bin/env python3
"""
Тест правильной инициализации системы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_antiban import get_advanced_system

def test_initialization():
    """Тест правильной инициализации системы"""
    
    print("🧪 ТЕСТ ПРАВИЛЬНОЙ ИНИЦИАЛИЗАЦИИ")
    print("=" * 60)
    
    # Получаем экземпляр системы
    system = get_advanced_system()
    
    print(f"📊 Начальные значения:")
    print(f"   proxy_mode: {system.proxy_mode}")
    print(f"   current_proxy: {system.current_proxy}")
    print(f"   http_requests: {system.http_requests}")
    print(f"   http_success: {system.http_success}")
    print(f"   errors_403: {system.errors_403}")
    print(f"   consecutive_errors: {system.consecutive_errors}")
    
    # Проверяем, должна ли система использовать прокси
    should_use = system._should_use_proxy()
    print(f"\n🔍 Должна ли использовать прокси: {should_use}")
    
    # Получаем статистику
    stats = system.get_stats()
    
    print(f"\n📊 Статистика из get_stats():")
    print(f"   no_proxy_requests: {stats.get('no_proxy_requests', 0)}")
    print(f"   no_proxy_success: {stats.get('no_proxy_success', 0)}")
    print(f"   proxy_requests: {stats.get('proxy_requests', 0)}")
    print(f"   proxy_success: {stats.get('proxy_success', 0)}")
    
    # Симулируем отображение статуса
    print(f"\n📊 СИМУЛЯЦИЯ СТАТУСА:")
    no_proxy_success = stats.get('no_proxy_success', 0)
    no_proxy_requests = stats.get('no_proxy_requests', 0)
    proxy_success = stats.get('proxy_success', 0)
    proxy_requests = stats.get('proxy_requests', 0)
    
    print(f"🚀 Продвинутая система:")
    print(f"   📊 HTTP (без прокси): {no_proxy_success}/{no_proxy_requests}")
    print(f"   📊 HTTP (с прокси): {proxy_success}/{proxy_requests}")
    print(f"   🔄 Режим: {system.proxy_mode}")
    
    # Анализируем правильность инициализации
    if system.proxy_mode == "auto" and system.current_proxy is None:
        print(f"\n✅ ИНИЦИАЛИЗАЦИЯ ПРАВИЛЬНАЯ:")
        print(f"   - Режим: auto (экономия трафика)")
        print(f"   - Прокси: отключен")
        print(f"   - Система готова к работе без прокси")
    else:
        print(f"\n❌ ИНИЦИАЛИЗАЦИЯ НЕПРАВИЛЬНАЯ:")
        print(f"   - Режим: {system.proxy_mode}")
        print(f"   - Прокси: {system.current_proxy}")
        print(f"   - Система должна начинать в режиме auto без прокси")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_initialization() 