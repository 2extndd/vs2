#!/usr/bin/env python3
"""
Тест базовой системы Vinted Scanner (без прокси)
"""

import sys
import time
import requests
import random
from datetime import datetime
sys.path.append('.')

import Config
import vinted_scanner

class BasicSystemTest:
    def __init__(self):
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'errors_403': 0,
            'errors_429': 0,
            'errors_401': 0,
            'other_errors': 0,
            'items_found': 0,
            'response_times': []
        }
        
    def test_basic_request(self, topic_name, params):
        """Тест базового запроса без прокси"""
        start_time = time.time()
        
        try:
            print(f"🔍 Базовый тест: {topic_name}")
            print(f"📋 Параметры: {params}")
            
            # Создаем сессию
            session = requests.Session()
            
            # Получаем cookies с правильными заголовками
            headers = vinted_scanner.vinted_antiblock.get_headers()
            main_response = session.get(Config.vinted_url, headers=headers, timeout=30)
            cookies = session.cookies.get_dict()
            print(f"🍪 Cookies получены: {len(cookies)}")
            
            if len(cookies) == 0:
                print("⚠️ Cookies не получены, пробуем альтернативный способ...")
                # Альтернативный способ получения cookies
                session.post(Config.vinted_url, headers=headers, timeout=30)
                cookies = session.cookies.get_dict()
                print(f"🍪 Cookies после POST: {len(cookies)}")
            
            # HTTP запрос без прокси
            url = f"{Config.vinted_url}/api/v2/catalog/items"
            response = session.get(
                url,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=30
            )
            
            response_time = time.time() - start_time
            self.results['response_times'].append(response_time)
            
            print(f"📊 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                self.results['successful_requests'] += 1
                self.results['items_found'] += len(items)
                
                print(f"✅ УСПЕХ: {len(items)} товаров за {response_time:.2f}s")
                if items:
                    for i, item in enumerate(items[:3], 1):
                        title = item.get('title', 'N/A')
                        price = item.get('price', {})
                        amount = price.get('amount', 'N/A')
                        currency = price.get('currency_code', '')
                        brand = item.get('brand_title', 'N/A')
                        print(f"   {i}. {title}")
                        print(f"      💰 {amount} {currency}")
                        print(f"      🏷️ {brand}")
            elif response.status_code == 403:
                self.results['errors_403'] += 1
                self.results['failed_requests'] += 1
                print(f"❌ HTTP 403 Forbidden за {response_time:.2f}s")
            elif response.status_code == 429:
                self.results['errors_429'] += 1
                self.results['failed_requests'] += 1
                print(f"❌ HTTP 429 Too Many Requests за {response_time:.2f}s")
            elif response.status_code == 401:
                self.results['errors_401'] += 1
                self.results['failed_requests'] += 1
                print(f"❌ HTTP 401 Unauthorized за {response_time:.2f}s")
                print(f"📝 Ответ: {response.text[:200]}")
            else:
                self.results['other_errors'] += 1
                self.results['failed_requests'] += 1
                print(f"❌ HTTP {response.status_code} за {response_time:.2f}s")
                
        except Exception as e:
            self.results['failed_requests'] += 1
            print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
            
        self.results['total_requests'] += 1
        
    def test_multiple_requests(self):
        """Тест нескольких запросов"""
        print(f"\n🚀 ТЕСТ БАЗОВОЙ СИСТЕМЫ (без прокси)")
        print("=" * 50)
        
        # Параметры для тестирования
        test_cases = [
            {
                'name': 'Prada',
                'params': {
                    'page': '1', 'per_page': '2', 'search_text': '',
                    'catalog_ids': '2050,1231,82', 'brand_ids': '3573',
                    'order': 'newest_first', 'price_to': '80'
                }
            },
            {
                'name': 'bags',
                'params': {
                    'page': '1', 'per_page': '2', 'search_text': '',
                    'catalog_ids': '', 'brand_ids': '212366',
                    'order': 'newest_first', 'price_to': '45'
                }
            },
            {
                'name': 'Alexander Wang',
                'params': {
                    'page': '1', 'per_page': '2', 'search_text': 'Leather',
                    'catalog_ids': '94', 'brand_ids': '28327',
                    'order': 'newest_first', 'price_to': '90'
                }
            }
        ]
        
        # Выполняем запросы
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Тест {i}/{len(test_cases)} ---")
            self.test_basic_request(test_case['name'], test_case['params'])
            
            # Пауза между запросами
            if i < len(test_cases):
                delay = random.uniform(3, 5)
                print(f"⏱️ Пауза {delay:.1f}s...")
                time.sleep(delay)
                
    def print_results(self):
        """Вывод результатов"""
        print(f"\n📊 РЕЗУЛЬТАТЫ БАЗОВОЙ СИСТЕМЫ")
        print("=" * 40)
        
        total = self.results['total_requests']
        success = self.results['successful_requests']
        failed = self.results['failed_requests']
        
        print(f"📈 Всего запросов: {total}")
        print(f"✅ Успешных: {success}")
        print(f"❌ Неудачных: {failed}")
        print(f"📊 Успешность: {(success/total*100):.1f}%" if total > 0 else "📊 Успешность: 0%")
        
        if self.results['response_times']:
            avg_time = sum(self.results['response_times']) / len(self.results['response_times'])
            min_time = min(self.results['response_times'])
            max_time = max(self.results['response_times'])
            print(f"⏱️ Среднее время ответа: {avg_time:.2f}s")
            print(f"⏱️ Минимальное время: {min_time:.2f}s")
            print(f"⏱️ Максимальное время: {max_time:.2f}s")
            
        print(f"📦 Найдено товаров: {self.results['items_found']}")
        print(f"🚫 Ошибки 403: {self.results['errors_403']}")
        print(f"🚫 Ошибки 429: {self.results['errors_429']}")
        print(f"🚫 Ошибки 401: {self.results['errors_401']}")
        print(f"🚫 Другие ошибки: {self.results['other_errors']}")

def main():
    """Главная функция теста"""
    print("🧪 ТЕСТ БАЗОВОЙ СИСТЕМЫ VINTED SCANNER")
    print("=" * 50)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    basic_test = BasicSystemTest()
    
    try:
        # Тест базовой системы
        basic_test.test_multiple_requests()
        
        # Вывод результатов
        basic_test.print_results()
        
        print(f"\n✅ ТЕСТ БАЗОВОЙ СИСТЕМЫ ЗАВЕРШЕН!")
        print(f"🕐 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тест прерван пользователем")
        basic_test.print_results()
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 