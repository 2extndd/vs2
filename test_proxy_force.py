#!/usr/bin/env python3
"""
Принудительная проверка с разными прокси
"""

import requests
import time
import random

def test_proxy_force():
    """Тестируем Vinted с разными прокси"""
    print("🌐 ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА С ПРОКСИ")
    print("=" * 40)
    
    # Список прокси для тестирования
    proxies_list = [
        "136.243.177.154:23567",
        "175.110.113.245:15595", 
        "185.199.229.156:7492",
        "185.199.228.220:7492",
        "185.199.231.45:7492",
        "188.74.210.207:6286",
        "188.74.183.10:8279",
        "188.74.210.21:6100",
        "45.155.68.129:8133",
        "154.95.36.199:6893"
    ]
    
    test_url = "https://www.vinted.de/api/v2/catalog/items"
    params = {
        'page': '1',
        'per_page': '2',
        'search_text': '',
        'catalog_ids': '',
        'brand_ids': '',
        'order': 'newest_first',
        'price_to': '50'
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    success_count = 0
    total_count = 0
    
    print(f"🔍 Тестируем {len(proxies_list)} прокси...")
    print()
    
    for i, proxy in enumerate(proxies_list, 1):
        total_count += 1
        print(f"📋 Тест {i}/{len(proxies_list)}: {proxy}")
        
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get(
                test_url, 
                params=params, 
                headers=headers, 
                proxies=proxy_dict, 
                timeout=15
            )
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                success_count += 1
                print(f"   ✅ УСПЕХ! Прокси работает!")
                try:
                    data = response.json()
                    items_count = len(data.get('items', []))
                    print(f"   📦 Получено товаров: {items_count}")
                except:
                    print(f"   📦 Данные получены (не JSON)")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                if response.status_code == 403:
                    print(f"   🚫 Vinted блокирует этот прокси")
                elif response.status_code == 429:
                    print(f"   ⏰ Слишком много запросов")
                else:
                    print(f"   📄 Ответ: {response.text[:50]}...")
                    
        except requests.exceptions.ProxyError:
            print(f"   ❌ Ошибка прокси: соединение не установлено")
        except requests.exceptions.ConnectTimeout:
            print(f"   ⏰ Таймаут: прокси не отвечает")
        except requests.exceptions.ReadTimeout:
            print(f"   ⏰ Таймаут чтения: прокси медленный")
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:50]}")
        
        print()
        time.sleep(1)  # Пауза между запросами
    
    # Итоги
    print("=" * 40)
    print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"   Всего прокси: {total_count}")
    print(f"   Успешных: {success_count}")
    print(f"   Неудачных: {total_count - success_count}")
    print(f"   Успешность: {(success_count/total_count)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n✅ НАЙДЕНЫ РАБОТАЮЩИЕ ПРОКСИ!")
        print(f"   Рекомендация: /recovery force_proxy")
    else:
        print(f"\n❌ НЕТ РАБОТАЮЩИХ ПРОКСИ")
        print(f"   Рекомендация: /recovery force_noproxy")
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_proxy_force() 