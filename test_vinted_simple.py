#!/usr/bin/env python3
"""
Простой тест доступности Vinted
"""

import requests
import time

def test_vinted_simple():
    """Простой тест Vinted"""
    print("🌐 ПРОСТОЙ ТЕСТ VINTED")
    print("=" * 30)
    
    # Тест 1: Основной сайт
    print(f"\n📋 Тест 1: Основной сайт")
    try:
        response = requests.get("https://www.vinted.de", timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Vinted работает!")
        else:
            print(f"   ❌ Vinted недоступен: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 2: С задержкой
    print(f"\n📋 Тест 2: С задержкой (5 сек)")
    time.sleep(5)
    try:
        response = requests.get("https://www.vinted.de", timeout=10)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Vinted работает!")
        else:
            print(f"   ❌ Vinted недоступен: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:50]}")
    
    # Тест 3: Другие домены Vinted
    print(f"\n📋 Тест 3: Другие домены")
    
    domains = [
        "https://www.vinted.com",
        "https://www.vinted.fr", 
        "https://www.vinted.it",
        "https://www.vinted.es"
    ]
    
    for domain in domains:
        try:
            response = requests.get(domain, timeout=5)
            print(f"   {domain}: {response.status_code}")
        except Exception as e:
            print(f"   {domain}: ❌ {str(e)[:30]}")
    
    # Тест 4: Проверка интернета
    print(f"\n📋 Тест 4: Проверка интернета")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"   Google: {response.status_code} ✅")
    except Exception as e:
        print(f"   Google: ❌ {str(e)[:30]}")
    
    try:
        response = requests.get("https://www.github.com", timeout=5)
        print(f"   GitHub: {response.status_code} ✅")
    except Exception as e:
        print(f"   GitHub: ❌ {str(e)[:30]}")
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_vinted_simple() 