#!/usr/bin/env python3
"""
Тест прямого доступа к Vinted
"""

import requests
import time

def test_direct_vinted():
    """Тестируем прямой доступ к Vinted"""
    print("🌐 ТЕСТ ПРЯМОГО ДОСТУПА К VINTED")
    print("=" * 40)
    
    # Разные User-Agent для тестирования
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ]
    
    # Разные домены Vinted
    vinted_domains = [
        "https://www.vinted.de",
        "https://www.vinted.com", 
        "https://www.vinted.fr",
        "https://www.vinted.it",
        "https://www.vinted.es"
    ]
    
    success_count = 0
    total_count = 0
    
    print(f"🔍 Тестируем {len(vinted_domains)} доменов с {len(user_agents)} User-Agent...")
    print()
    
    for domain in vinted_domains:
        for i, user_agent in enumerate(user_agents, 1):
            total_count += 1
            print(f"📋 Тест {total_count}: {domain} (UA {i})")
            
            try:
                headers = {
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                # Сначала получаем cookies
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(domain, timeout=10)
                print(f"   Статус: {response.status_code}")
                print(f"   Cookies: {len(session.cookies)}")
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"   ✅ УСПЕХ! Домен работает!")
                    
                    # Тестируем API
                    api_url = f"{domain}/api/v2/catalog/items"
                    params = {
                        'page': '1',
                        'per_page': '2',
                        'search_text': '',
                        'catalog_ids': '',
                        'brand_ids': '',
                        'order': 'newest_first',
                        'price_to': '50'
                    }
                    
                    api_response = session.get(api_url, params=params, timeout=10)
                    print(f"   API статус: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        print(f"   ✅ API работает!")
                        try:
                            data = api_response.json()
                            items_count = len(data.get('items', []))
                            print(f"   📦 Получено товаров: {items_count}")
                        except:
                            print(f"   📦 API данные получены")
                    else:
                        print(f"   ❌ API ошибка: {api_response.status_code}")
                        
                else:
                    print(f"   ❌ Ошибка: {response.status_code}")
                    if response.status_code == 403:
                        print(f"   🚫 Vinted блокирует этот User-Agent")
                    elif response.status_code == 429:
                        print(f"   ⏰ Слишком много запросов")
                    else:
                        print(f"   📄 Ответ: {response.text[:50]}...")
                        
            except requests.exceptions.ConnectTimeout:
                print(f"   ⏰ Таймаут соединения")
            except requests.exceptions.ReadTimeout:
                print(f"   ⏰ Таймаут чтения")
            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)[:50]}")
            
            print()
            time.sleep(2)  # Пауза между запросами
    
    # Итоги
    print("=" * 40)
    print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"   Всего тестов: {total_count}")
    print(f"   Успешных: {success_count}")
    print(f"   Неудачных: {total_count - success_count}")
    print(f"   Успешность: {(success_count/total_count)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n✅ НАЙДЕН РАБОТАЮЩИЙ ДОСТУП!")
        print(f"   Рекомендация: /recovery force_noproxy")
    else:
        print(f"\n❌ НЕТ РАБОТАЮЩЕГО ДОСТУПА")
        print(f"   Vinted полностью заблокирован")
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_direct_vinted() 