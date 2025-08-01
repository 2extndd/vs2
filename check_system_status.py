#!/usr/bin/env python3
"""
Проверка состояния системы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner

def check_system_status():
    """Проверяем состояние системы"""
    print("🔍 ПРОВЕРКА СОСТОЯНИЯ СИСТЕМЫ")
    print("=" * 40)
    
    print(f"📊 ТЕКУЩЕЕ СОСТОЯНИЕ:")
    print(f"   Система: {vinted_scanner.current_system}")
    print(f"   Ошибки базовой: {vinted_scanner.basic_system_errors}")
    print(f"   Ошибки без прокси: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   Ошибки с прокси: {vinted_scanner.advanced_proxy_errors}")
    
    # Проверяем прокси
    if hasattr(vinted_scanner, 'advanced_system') and vinted_scanner.advanced_system:
        proxy_count = len(vinted_scanner.advanced_system.proxies) if hasattr(vinted_scanner.advanced_system, 'proxies') else 0
        print(f"   Прокси доступны: {proxy_count}")
        
        # Проверяем здоровье прокси
        healthy_proxies = 0
        dead_proxies = 0
        if hasattr(vinted_scanner.advanced_system, 'proxies'):
            for proxy in vinted_scanner.advanced_system.proxies:
                health = proxy.get('health_score', 0)
                if health > 0:
                    healthy_proxies += 1
                else:
                    dead_proxies += 1
        
        print(f"   Здоровых прокси: {healthy_proxies}")
        print(f"   Мертвых прокси: {dead_proxies}")
        
        # Текущий прокси
        current_proxy = vinted_scanner.advanced_system.current_proxy
        if current_proxy:
            health = current_proxy.get('health_score', 0)
            print(f"   Текущий прокси: {current_proxy.get('host', 'Unknown')}:{current_proxy.get('port', 'Unknown')} (здоровье: {health})")
        else:
            print(f"   Текущий прокси: не установлен")
    else:
        print(f"   Продвинутая система недоступна")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 20)
    
    if vinted_scanner.advanced_proxy_errors > 100:
        print(f"   ⚠️ Очень много ошибок прокси ({vinted_scanner.advanced_proxy_errors})")
        print(f"   🔧 Попробуйте: /recovery force_noproxy")
    
    if vinted_scanner.basic_system_errors > 50:
        print(f"   ⚠️ Много ошибок базовой системы ({vinted_scanner.basic_system_errors})")
        print(f"   🔧 Попробуйте: /reset")
    
    if dead_proxies > healthy_proxies:
        print(f"   ⚠️ Больше мертвых прокси ({dead_proxies}) чем здоровых ({healthy_proxies})")
        print(f"   🔧 Попробуйте: /recovery force_noproxy")
    
    print(f"   🔧 Общий сброс: /reset")
    print(f"   🔧 Восстановление: /recovery")
    
    print(f"\n✅ ПРОВЕРКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    check_system_status() 