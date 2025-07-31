#!/usr/bin/env python3
"""
Тест умной самовосстанавливающейся системы
Проверяет автоматическое переключение режимов и восстановление прокси
"""

import time
import logging
import requests
from advanced_antiban import get_advanced_system

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def test_smart_recovery_system():
    """Тест умной самовосстанавливающейся системы"""
    print("🧠 ТЕСТ УМНОЙ САМОВОССТАНАВЛИВАЮЩЕЙСЯ СИСТЕМЫ")
    print("=" * 60)
    
    # Инициализация системы
    system = get_advanced_system()
    print(f"✅ Система инициализирована (ID: {id(system)})")
    
    # Показываем начальную статистику
    stats = system.get_stats()
    print(f"\n📊 НАЧАЛЬНАЯ СТАТИСТИКА:")
    print(f"• Прокси загружено: {stats['proxies_count']}")
    print(f"• Режим прокси: {stats['proxy_mode']}")
    print(f"• Whitelist: {stats['proxy_whitelist_count']}")
    print(f"• Blacklist: {stats['proxy_blacklist_count']}")
    
    # Тест 1: Проверка автоматического переключения режимов
    print(f"\n🔄 ТЕСТ 1: АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ")
    print("-" * 40)
    
    # Симулируем ошибки для отключения прокси
    print("📊 Симулируем ошибки для отключения прокси...")
    for i in range(10):
        system.errors_403 += 1
        system.proxy_failures += 1
        time.sleep(0.1)
    
    # Запускаем проверку здоровья
    system._periodic_proxy_health_check()
    
    stats = system.get_stats()
    print(f"• Новый режим прокси: {stats['proxy_mode']}")
    print(f"• Переключений режимов: {stats['mode_switch_count']}")
    
    # Тест 2: Восстановление прокси
    print(f"\n🔄 ТЕСТ 2: ВОССТАНОВЛЕНИЕ ПРОКСИ")
    print("-" * 40)
    
    # Симулируем успехи для включения прокси
    print("📊 Симулируем успехи для включения прокси...")
    for i in range(5):
        system.http_success += 1
        system.proxy_successes += 1
        time.sleep(0.1)
    
    # Запускаем проверку здоровья
    system._periodic_proxy_health_check()
    
    stats = system.get_stats()
    print(f"• Новый режим прокси: {stats['proxy_mode']}")
    print(f"• Переключений режимов: {stats['mode_switch_count']}")
    
    # Тест 3: Тестирование прокси
    print(f"\n🔄 ТЕСТ 3: ТЕСТИРОВАНИЕ ПРОКСИ")
    print("-" * 40)
    
    working_proxies = []
    failed_proxies = []
    
    for proxy in system.proxies[:5]:  # Тестируем первые 5 прокси
        if system._test_proxy(proxy):
            working_proxies.append(f"{proxy['host']}:{proxy['port']}")
            if proxy not in system.proxy_whitelist:
                system.proxy_whitelist.append(proxy)
        else:
            failed_proxies.append(f"{proxy['host']}:{proxy['port']}")
            if proxy not in system.proxy_blacklist:
                system.proxy_blacklist.append(proxy)
    
    print(f"✅ Рабочих прокси: {len(working_proxies)}")
    print(f"❌ Неисправных прокси: {len(failed_proxies)}")
    
    if working_proxies:
        print("✅ РАБОЧИЕ ПРОКСИ:")
        for proxy in working_proxies:
            print(f"• {proxy}")
    
    # Тест 4: Обновление здоровья прокси
    print(f"\n🔄 ТЕСТ 4: ОБНОВЛЕНИЕ ЗДОРОВЬЯ ПРОКСИ")
    print("-" * 40)
    
    if system.proxies:
        test_proxy = system.proxies[0]
        print(f"📊 Тестируем прокси: {test_proxy['host']}:{test_proxy['port']}")
        print(f"• Начальное здоровье: {test_proxy['health_score']}")
        
        # Симулируем успехи
        for i in range(3):
            system._update_proxy_health(test_proxy, True)
            print(f"• Здоровье после успеха {i+1}: {test_proxy['health_score']}")
        
        # Симулируем ошибки
        for i in range(2):
            system._update_proxy_health(test_proxy, False)
            print(f"• Здоровье после ошибки {i+1}: {test_proxy['health_score']}")
    
    # Тест 5: Попытка восстановления
    print(f"\n🔄 ТЕСТ 5: ПОПЫТКА ВОССТАНОВЛЕНИЯ")
    print("-" * 40)
    
    system.proxy_mode = "disabled"
    system.proxy_recovery_attempts = 0
    
    print("📊 Запускаем попытку восстановления...")
    system._attempt_proxy_recovery()
    
    stats = system.get_stats()
    print(f"• Попыток восстановления: {stats['proxy_recovery_attempts']}")
    print(f"• Whitelist: {stats['proxy_whitelist_count']}")
    print(f"• Blacklist: {stats['proxy_blacklist_count']}")
    
    # Финальная статистика
    print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    print("=" * 60)
    
    stats = system.get_stats()
    print(f"• HTTP запросы: {stats['http_success']}/{stats['http_requests']}")
    print(f"• Успешность: {stats['success_rate']:.1f}%")
    print(f"• Режим прокси: {stats['proxy_mode']}")
    print(f"• Whitelist: {stats['proxy_whitelist_count']}")
    print(f"• Blacklist: {stats['proxy_blacklist_count']}")
    print(f"• Переключений режимов: {stats['mode_switch_count']}")
    print(f"• Попыток восстановления: {stats['proxy_recovery_attempts']}")
    
    # Статистика прокси с здоровьем
    print(f"\n📊 СТАТИСТИКА ПРОКСИ:")
    for proxy, proxy_stat in stats['proxy_stats'].items():
        if proxy_stat['requests'] > 0:
            health_emoji = "🟢" if proxy_stat['health_score'] >= 80 else "🟡" if proxy_stat['health_score'] >= 50 else "🔴"
            print(f"{health_emoji} {proxy}: {proxy_stat['success']}/{proxy_stat['requests']} ({proxy_stat['success_rate']:.1f}%) [Здоровье: {proxy_stat['health_score']}]")
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН!")
    return system

def test_real_requests():
    """Тест реальных запросов через систему"""
    print(f"\n🌐 ТЕСТ РЕАЛЬНЫХ ЗАПРОСОВ")
    print("=" * 60)
    
    system = get_advanced_system()
    
    # Тестовый URL
    test_url = "https://httpbin.org/ip"
    test_params = {}
    
    print(f"📊 Тестируем запрос к: {test_url}")
    
    # Делаем несколько запросов
    for i in range(3):
        print(f"\n🔄 Запрос {i+1}/3:")
        
        try:
            result = system.make_http_request(test_url, test_params)
            if result:
                print(f"✅ Успех! Ответ: {result}")
            else:
                print(f"❌ Ошибка запроса")
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        time.sleep(2)
    
    # Показываем статистику
    stats = system.get_stats()
    print(f"\n📊 СТАТИСТИКА ПОСЛЕ РЕАЛЬНЫХ ЗАПРОСОВ:")
    print(f"• HTTP запросы: {stats['http_success']}/{stats['http_requests']}")
    print(f"• Успешность: {stats['success_rate']:.1f}%")
    print(f"• Режим прокси: {stats['proxy_mode']}")
    print(f"• Использует прокси: {'Да' if stats['should_use_proxy'] else 'Нет'}")

if __name__ == "__main__":
    try:
        # Основной тест системы
        system = test_smart_recovery_system()
        
        # Тест реальных запросов
        test_real_requests()
        
        print(f"\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        logging.error(f"Ошибка в тестах: {e}") 