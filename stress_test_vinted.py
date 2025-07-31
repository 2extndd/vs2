#!/usr/bin/env python3
"""
Стресс-тест системы Vinted Scanner
Проверяет реальную работу с Vinted API
"""

import sys
import time
import asyncio
import threading
import random
import json
from datetime import datetime
sys.path.append('.')

import Config
from advanced_antiban import get_advanced_system
import vinted_scanner

class VintedStressTest:
    def __init__(self):
        self.advanced_system = get_advanced_system()
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'errors_403': 0,
            'errors_429': 0,
            'errors_401': 0,
            'other_errors': 0,
            'items_found': 0,
            'response_times': [],
            'proxy_rotations': 0
        }
        
    def test_single_request(self, topic_name, params):
        """Тест одного запроса"""
        start_time = time.time()
        
        try:
            print(f"🔍 Тест: {topic_name}")
            print(f"📋 Параметры: {params}")
            
            # HTTP запрос через продвинутую систему
            url = f"{Config.vinted_url}/api/v2/catalog/items"
            result = self.advanced_system.make_http_request(url, params)
            
            response_time = time.time() - start_time
            self.results['response_times'].append(response_time)
            
            if result:
                items = result.get('items', [])
                self.results['successful_requests'] += 1
                self.results['items_found'] += len(items)
                
                print(f"✅ УСПЕХ: {len(items)} товаров за {response_time:.2f}s")
                if items:
                    for i, item in enumerate(items[:2], 1):
                        title = item.get('title', 'N/A')
                        price = item.get('price', {})
                        amount = price.get('amount', 'N/A')
                        currency = price.get('currency_code', '')
                        print(f"   {i}. {title} - {amount} {currency}")
            else:
                self.results['failed_requests'] += 1
                print(f"❌ ОШИБКА: Нет данных за {response_time:.2f}s")
                
        except Exception as e:
            self.results['failed_requests'] += 1
            print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
            
        self.results['total_requests'] += 1
        
    def test_concurrent_requests(self, num_requests=10):
        """Тест параллельных запросов"""
        print(f"\n🚀 СТРЕСС-ТЕСТ: {num_requests} параллельных запросов")
        print("=" * 60)
        
        # Параметры для тестирования
        test_params = [
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
        for i in range(num_requests):
            test_case = random.choice(test_params)
            self.test_single_request(test_case['name'], test_case['params'])
            
            # Небольшая задержка между запросами
            if i < num_requests - 1:
                delay = random.uniform(1, 3)
                print(f"⏱️ Пауза {delay:.1f}s...")
                time.sleep(delay)
                
    def test_proxy_rotation(self):
        """Тест ротации прокси"""
        print(f"\n🔄 ТЕСТ РОТАЦИИ ПРОКСИ")
        print("=" * 40)
        
        initial_proxy = self.advanced_system.current_proxy
        if initial_proxy:
            print(f"📡 Начальный прокси: {initial_proxy['host']}:{initial_proxy['port']}")
        else:
            print("📡 Начальный прокси: ❌ Отключен")
        
        # Принудительная ротация прокси
        for i in range(5):
            old_proxy = self.advanced_system.current_proxy
            self.advanced_system._rotate_proxy()
            new_proxy = self.advanced_system.current_proxy
            
            if old_proxy != new_proxy:
                if new_proxy:
                    print(f"✅ Ротация {i+1}: {new_proxy['host']}:{new_proxy['port']}")
                else:
                    print(f"✅ Ротация {i+1}: ❌ Отключен")
                self.results['proxy_rotations'] += 1
            else:
                if new_proxy:
                    print(f"⚠️ Ротация {i+1}: Тот же прокси {new_proxy['host']}:{new_proxy['port']}")
                else:
                    print(f"⚠️ Ротация {i+1}: Прокси отключен")
                
    def test_error_handling(self):
        """Тест обработки ошибок"""
        print(f"\n🚨 ТЕСТ ОБРАБОТКИ ОШИБОК")
        print("=" * 40)
        
        # Тест с неверными параметрами
        invalid_params = {
            'page': '999', 'per_page': '999', 'search_text': 'INVALID_TEST',
            'catalog_ids': '999999', 'brand_ids': '999999',
            'order': 'newest_first', 'price_to': '999999'
        }
        
        print("🔍 Тест с неверными параметрами...")
        self.test_single_request("INVALID_TEST", invalid_params)
        
        # Проверяем статистику ошибок
        stats = self.advanced_system.get_stats()
        print(f"📊 Ошибки 403: {stats['errors_403']}")
        print(f"📊 Ошибки 429: {stats['errors_429']}")
        print(f"📊 Ошибки 521: {stats['errors_521']}")
        
    def test_system_stability(self, duration=60):
        """Тест стабильности системы"""
        print(f"\n🛡️ ТЕСТ СТАБИЛЬНОСТИ ({duration}s)")
        print("=" * 40)
        
        start_time = time.time()
        requests_made = 0
        
        while time.time() - start_time < duration:
            try:
                # Случайный запрос
                params = {
                    'page': '1', 'per_page': '2', 'search_text': '',
                    'catalog_ids': '', 'brand_ids': '212366',
                    'order': 'newest_first', 'price_to': '45'
                }
                
                self.test_single_request("STABILITY_TEST", params)
                requests_made += 1
                
                # Пауза между запросами
                time.sleep(random.uniform(2, 5))
                
            except KeyboardInterrupt:
                print("\n⏹️ Тест прерван пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка в тесте стабильности: {e}")
                
        print(f"📊 Запросов за {duration}s: {requests_made}")
        
    def print_results(self):
        """Вывод результатов тестирования"""
        print(f"\n📊 РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТА")
        print("=" * 50)
        
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
        print(f"🔄 Ротаций прокси: {self.results['proxy_rotations']}")
        
        # Статистика продвинутой системы
        stats = self.advanced_system.get_stats()
        print(f"\n🚀 СТАТИСТИКА ПРОДВИНУТОЙ СИСТЕМЫ:")
        print(f"   📊 HTTP запросы: {stats['http_success']}/{stats['http_requests']}")
        print(f"   📈 Успешность: {stats['success_rate']:.1f}%")
        print(f"   📡 Прокси: {stats['proxies_count']} активных")
        print(f"   ⚠️ Ошибок подряд: {stats['consecutive_errors']}")
        print(f"   🔄 Текущий прокси: {stats['current_proxy']}")
        
        # Статистика прокси
        if stats.get('proxy_stats'):
            print(f"\n📊 СТАТИСТИКА ПРОКСИ:")
            for proxy, proxy_stat in stats['proxy_stats'].items():
                print(f"   • {proxy}: {proxy_stat['success']}/{proxy_stat['requests']} ({proxy_stat['success_rate']:.1f}%)")

def main():
    """Главная функция стресс-теста"""
    print("🧪 СТРЕСС-ТЕСТ СИСТЕМЫ VINTED SCANNER")
    print("=" * 60)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    stress_test = VintedStressTest()
    
    try:
        # Тест 1: Ротация прокси
        stress_test.test_proxy_rotation()
        
        # Тест 2: Параллельные запросы
        stress_test.test_concurrent_requests(num_requests=15)
        
        # Тест 3: Обработка ошибок
        stress_test.test_error_handling()
        
        # Тест 4: Стабильность (30 секунд)
        stress_test.test_system_stability(duration=30)
        
        # Вывод результатов
        stress_test.print_results()
        
        print(f"\n✅ СТРЕСС-ТЕСТ ЗАВЕРШЕН!")
        print(f"🕐 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тест прерван пользователем")
        stress_test.print_results()
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 