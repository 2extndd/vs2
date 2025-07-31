#!/usr/bin/env python3
"""
Тест продвинутой антибан системы
"""

import asyncio
import time
import Config
from antiban import antiban_system, ProxyConfig

async def test_advanced_antiban():
    """Тест продвинутой антибан системы"""
    print("🧪 Тест продвинутой антибан системы")
    print("=" * 50)
    
    # Проверяем конфигурацию
    print("\n📋 Проверка конфигурации:")
    print(f"  Продвинутая антибан: {'✅' if Config.advanced_antiban_enabled else '❌'}")
    print(f"  Прокси включены: {'✅' if Config.proxy_config['enabled'] else '❌'}")
    print(f"  Количество прокси: {len(Config.proxy_config['proxies'])}")
    print(f"  Ротация каждые: {Config.proxy_config['rotation_interval']} запросов")
    
    # Проверяем инициализацию
    print("\n🔧 Проверка инициализации:")
    print(f"  Система создана: {'✅' if antiban_system else '❌'}")
    print(f"  Количество сессий: {len(antiban_system.sessions)}")
    print(f"  Текущая сессия: {antiban_system.current_session_index}")
    
    # Тест 1: Проверка прокси конфигурации
    print("\n🌐 Тест 1: Конфигурация прокси")
    for i, proxy_data in enumerate(Config.proxy_config['proxies']):
        proxy = ProxyConfig(
            host=proxy_data['host'],
            port=proxy_data['port'],
            username=proxy_data['username'],
            password=proxy_data['password'],
            country=proxy_data['country'],
            type=proxy_data['type']
        )
        print(f"  ✅ Прокси {i+1}: {proxy.host}:{proxy.port} ({proxy.country})")
    
    # Тест 2: Симуляция запросов
    print("\n🔄 Тест 2: Симуляция запросов")
    test_params = {
        'page': '1',
        'per_page': '2',
        'search_text': 'test',
        'order': 'newest_first'
    }
    
    for i in range(3):
        print(f"  Запрос {i+1}...")
        try:
            result = await antiban_system.get_vinted_items(test_params)
            if result:
                print(f"    ✅ Успешно получено данных")
            else:
                print(f"    ❌ Нет данных")
        except Exception as e:
            print(f"    ❌ Ошибка: {str(e)[:50]}")
        
        # Небольшая пауза между запросами
        await asyncio.sleep(2)
    
    # Тест 3: Проверка статистики
    print("\n📊 Тест 3: Статистика")
    stats = antiban_system.get_stats()
    print(f"  Всего запросов: {stats['total_requests']}")
    print(f"  Всего ошибок: {stats['total_errors']}")
    print(f"  Всего блокировок: {stats['total_blocks']}")
    print(f"  Процент успеха: {stats['success_rate']:.1f}%")
    print(f"  Текущая сессия: {stats['current_session']}/{stats['sessions_count']}")
    
    # Тест 4: Проверка ротации сессий
    print("\n🔄 Тест 4: Ротация сессий")
    old_session = antiban_system.current_session_index
    await antiban_system._rotate_session()
    new_session = antiban_system.current_session_index
    
    if old_session != new_session:
        print(f"  ✅ Ротация успешна: {old_session} -> {new_session}")
    else:
        print(f"  ⚠️ Ротация не произошла")
    
    # Тест 5: Проверка обработки ошибок
    print("\n❌ Тест 5: Обработка ошибок")
    try:
        # Симулируем ошибку
        await antiban_system._handle_error("Test error", 403)
        print(f"  ✅ Обработка ошибки успешна")
    except Exception as e:
        print(f"  ❌ Ошибка обработки: {str(e)[:50]}")
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    if Config.advanced_antiban_enabled:
        print("✅ Продвинутая антибан система: ВКЛЮЧЕНА")
    else:
        print("❌ Продвинутая антибан система: ОТКЛЮЧЕНА")
    
    if antiban_system:
        print("✅ Система инициализирована: УСПЕШНО")
    else:
        print("❌ Система инициализирована: ОШИБКА")
    
    if len(Config.proxy_config['proxies']) > 0:
        print("✅ Прокси настроены: ГОТОВО")
    else:
        print("❌ Прокси настроены: НЕ НАСТРОЕНЫ")
    
    print("\n🎯 Рекомендации:")
    if not Config.proxy_config['enabled']:
        print("  - Включите прокси в Config.py")
    if len(Config.proxy_config['proxies']) == 0:
        print("  - Добавьте реальные прокси в Config.py")
    if not Config.advanced_antiban_enabled:
        print("  - Включите advanced_antiban_enabled = True")
    
    print("\n🚀 Для использования:")
    print("  1. Установите зависимости: pip install -r requirements_advanced.txt")
    print("  2. Настройте реальные прокси в Config.py")
    print("  3. Запустите бота: python3 vinted_scanner.py")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_advanced_antiban()) 