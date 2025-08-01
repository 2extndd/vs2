#!/usr/bin/env python3
"""
Диагностика системы Vinted Scanner
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vinted_scanner
import requests
import time

def diagnose_system():
    """Диагностика системы"""
    print("🔍 ДИАГНОСТИКА СИСТЕМЫ")
    print("=" * 50)
    
    # Проверяем состояние систем
    print(f"📊 ТЕКУЩЕЕ СОСТОЯНИЕ:")
    print(f"   Текущая система: {vinted_scanner.current_system}")
    print(f"   Ошибки базовой: {vinted_scanner.basic_system_errors}")
    print(f"   Ошибки без прокси: {vinted_scanner.advanced_no_proxy_errors}")
    print(f"   Ошибки с прокси: {vinted_scanner.advanced_proxy_errors}")
    
    # Проверяем прокси
    if hasattr(vinted_scanner, 'advanced_system') and vinted_scanner.advanced_system:
        proxy_count = len(vinted_scanner.advanced_system.proxies) if hasattr(vinted_scanner.advanced_system, 'proxies') else 0
        print(f"   Прокси доступны: {proxy_count}")
        
        # Проверяем здоровье прокси
        healthy_proxies = 0
        if hasattr(vinted_scanner.advanced_system, 'proxies'):
            for proxy in vinted_scanner.advanced_system.proxies:
                if proxy.get('health_score', 0) > 0:
                    healthy_proxies += 1
        
        print(f"   Здоровых прокси: {healthy_proxies}/{proxy_count}")
    else:
        print(f"   Продвинутая система недоступна")
    
    # Тестируем доступность Vinted
    print(f"\n🌐 ТЕСТ ДОСТУПНОСТИ VINTED:")
    print("-" * 30)
    
    try:
        # Простой запрос к Vinted
        response = requests.get("https://www.vinted.de", timeout=10)
        print(f"   Статус Vinted: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Vinted доступен")
        else:
            print(f"   ⚠️ Vinted отвечает с кодом {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка доступа к Vinted: {str(e)[:50]}")
    
    # Тестируем получение cookies
    print(f"\n🍪 ТЕСТ ПОЛУЧЕНИЯ COOKIES:")
    print("-" * 30)
    
    try:
        session = requests.Session()
        response = session.get("https://www.vinted.de", timeout=10)
        cookies = session.cookies
        
        print(f"   Получено cookies: {len(cookies)}")
        if cookies:
            print(f"   ✅ Cookies получены")
        else:
            print(f"   ⚠️ Cookies не получены")
            
    except Exception as e:
        print(f"   ❌ Ошибка получения cookies: {str(e)[:50]}")
    
    # Проверяем логику переключения
    print(f"\n🔄 ТЕСТ ЛОГИКИ ПЕРЕКЛЮЧЕНИЯ:")
    print("-" * 30)
    
    # Симулируем ошибки для тестирования переключения
    old_system = vinted_scanner.current_system
    print(f"   Текущая система: {old_system}")
    
    # Добавляем ошибки для принудительного переключения
    if vinted_scanner.current_system == "basic":
        vinted_scanner.basic_system_errors = 3
    elif vinted_scanner.current_system == "advanced_no_proxy":
        vinted_scanner.advanced_no_proxy_errors = 3
    
    if vinted_scanner.should_switch_system():
        print(f"   🔄 Переключение: {old_system} → {vinted_scanner.current_system}")
    else:
        print(f"   ✅ Система остается: {vinted_scanner.current_system}")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 30)
    
    if vinted_scanner.advanced_proxy_errors > 10:
        print(f"   ⚠️ Много ошибок прокси - проверьте доступность прокси")
    
    if vinted_scanner.basic_system_errors > 5:
        print(f"   ⚠️ Много ошибок базовой системы - Vinted может блокировать")
    
    print(f"   🔧 Попробуйте команду /recovery для сброса системы")
    print(f"   🔧 Попробуйте команду /reset для полного сброса")
    
    print(f"\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    diagnose_system() 