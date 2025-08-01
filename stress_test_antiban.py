#!/usr/bin/env python3
"""
Стресс-тест системы антибана с переключениями
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import time
import random

def stress_test_antiban_system():
    """Стресс-тест системы антибана"""
    print("🔥 СТРЕСС-ТЕСТ СИСТЕМЫ АНТИБАНА")
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
    
    # Тест 1: Быстрые переключения
    print(f"\n📋 ТЕСТ 1: БЫСТРЫЕ ПЕРЕКЛЮЧЕНИЯ")
    print("-" * 40)
    
    switches = []
    for i in range(20):
        # Принудительно вызываем ошибки для переключения
        if vinted_scanner.current_system == "basic":
            vinted_scanner.basic_system_errors = 3
        elif vinted_scanner.current_system == "advanced_no_proxy":
            vinted_scanner.advanced_no_proxy_errors = 3
        
        old_system = vinted_scanner.current_system
        if vinted_scanner.should_switch_system():
            switches.append(f"{old_system} → {vinted_scanner.current_system}")
            print(f"🔄 Переключение {len(switches)}: {old_system} → {vinted_scanner.current_system}")
        
        time.sleep(0.1)
    
    print(f"✅ Быстрых переключений: {len(switches)}")
    
    # Тест 2: Реалистичные ошибки
    print(f"\n📋 ТЕСТ 2: РЕАЛИСТИЧНЫЕ ОШИБКИ")
    print("-" * 40)
    
    # Сбрасываем состояние
    vinted_scanner.current_system = "basic"
    vinted_scanner.basic_system_errors = 0
    vinted_scanner.advanced_no_proxy_errors = 0
    vinted_scanner.advanced_proxy_errors = 0
    
    realistic_switches = []
    for i in range(50):
        # Симулируем реалистичные ошибки
        if vinted_scanner.current_system == "basic":
            if random.random() < 0.3:  # 30% ошибок
                vinted_scanner.basic_system_errors += 1
            vinted_scanner.basic_requests += 1
            if random.random() < 0.7:  # 70% успешность
                vinted_scanner.basic_success += 1
        elif vinted_scanner.current_system == "advanced_no_proxy":
            if random.random() < 0.25:  # 25% ошибок
                vinted_scanner.advanced_no_proxy_errors += 1
            vinted_scanner.advanced_no_proxy_requests += 1
            if random.random() < 0.8:  # 80% успешность
                vinted_scanner.advanced_no_proxy_success += 1
        elif vinted_scanner.current_system == "advanced_proxy":
            if random.random() < 0.2:  # 20% ошибок
                vinted_scanner.advanced_proxy_errors += 1
            vinted_scanner.advanced_proxy_requests += 1
            if random.random() < 0.85:  # 85% успешность
                vinted_scanner.advanced_proxy_success += 1
        
        old_system = vinted_scanner.current_system
        if vinted_scanner.should_switch_system():
            realistic_switches.append(f"{old_system} → {vinted_scanner.current_system}")
            print(f"🔄 Реалистичное переключение {len(realistic_switches)}: {old_system} → {vinted_scanner.current_system}")
        
        if (i + 1) % 10 == 0:
            print(f"📊 Итерация {i+1}: {vinted_scanner.current_system} (ошибок: basic={vinted_scanner.basic_system_errors}, no_proxy={vinted_scanner.advanced_no_proxy_errors}, proxy={vinted_scanner.advanced_proxy_errors})")
    
    # Тест 3: Возврат к лучшей системе
    print(f"\n📋 ТЕСТ 3: ВОЗВРАТ К ЛУЧШЕЙ СИСТЕМЕ")
    print("-" * 40)
    
    # Симулируем хорошую статистику для возврата
    vinted_scanner.advanced_no_proxy_success = 15
    vinted_scanner.advanced_no_proxy_requests = 18
    vinted_scanner.advanced_no_proxy_errors = 1
    vinted_scanner.last_switch_time = time.time() - 70  # Прошло больше минуты
    
    old_system = vinted_scanner.current_system
    if vinted_scanner.should_switch_system():
        print(f"🔄 Возврат к лучшей системе: {old_system} → {vinted_scanner.current_system}")
    else:
        print(f"✅ Система остается: {vinted_scanner.current_system}")
    
    # Финальная статистика
    print(f"\n🎯 ФИНАЛЬНАЯ СТАТИСТИКА АНТИБАНА:")
    print(f"   Финальная система: {vinted_scanner.current_system}")
    print(f"   Быстрых переключений: {len(switches)}")
    print(f"   Реалистичных переключений: {len(realistic_switches)}")
    print(f"   Всего переключений: {len(switches) + len(realistic_switches)}")
    print(f"   Ошибок: basic={vinted_scanner.basic_system_errors}, no_proxy={vinted_scanner.advanced_no_proxy_errors}, proxy={vinted_scanner.advanced_proxy_errors}")
    print(f"   Успешных запросов: basic={vinted_scanner.basic_success}, no_proxy={vinted_scanner.advanced_no_proxy_success}, proxy={vinted_scanner.advanced_proxy_success}")
    
    print(f"\n✅ СТРЕСС-ТЕСТ АНТИБАНА ЗАВЕРШЕН!")

if __name__ == "__main__":
    stress_test_antiban_system() 