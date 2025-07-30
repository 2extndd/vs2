#!/usr/bin/env python3
"""
🎯 VintedScanner PayPal Auto-Reservation Module

Автоматическое резервирование товаров через PayPal на 15 минут
с последующей передачей ссылки для оплаты на другом аккаунте.
"""

import time
import json
import logging
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class VintedPayPalReservation:
    """Класс для автоматического резервирования товаров через PayPal"""
    
    def __init__(self, vinted_session_cookies: dict, user_agent: str):
        self.cookies = vinted_session_cookies
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.vinted.it/",
            "Origin": "https://www.vinted.it"
        }
        self.reservations = {}  # Хранение активных резерваций
        
    def get_item_details(self, item_id: str) -> Optional[Dict]:
        """Получение детальной информации о товаре"""
        try:
            url = f"https://www.vinted.it/api/v2/items/{item_id}"
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('item')
            else:
                logging.error(f"❌ Failed to get item details: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error getting item details: {e}")
            return None
    
    def get_shipping_options(self, item_id: str) -> Optional[Dict]:
        """Получение опций доставки для товара"""
        try:
            url = f"https://www.vinted.it/api/v2/items/{item_id}/shipping_options"
            response = requests.get(url, headers=self.headers, cookies=self.cookies)
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"❌ Failed to get shipping options: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error getting shipping options: {e}")
            return None
    
    def create_checkout_session(self, item_id: str, shipping_option_id: str) -> Optional[Dict]:
        """Создание сессии checkout (резервирование товара)"""
        try:
            # Данные для создания заказа
            checkout_data = {
                "item_id": int(item_id),
                "shipping_option_id": int(shipping_option_id),
                "payment_method": "paypal",  # Указываем PayPal как метод оплаты
                "message": "",  # Сообщение продавцу (опционально)
            }
            
            url = "https://www.vinted.it/api/v2/transactions"
            response = requests.post(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                json=checkout_data
            )
            
            if response.status_code == 201:  # Created
                transaction = response.json()
                logging.info(f"✅ Checkout session created: {transaction.get('id')}")
                return transaction
            else:
                logging.error(f"❌ Failed to create checkout: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error creating checkout session: {e}")
            return None
    
    def get_paypal_payment_url(self, transaction_id: str) -> Optional[str]:
        """Получение ссылки для оплаты через PayPal"""
        try:
            # Запрос на получение PayPal URL
            url = f"https://www.vinted.it/api/v2/transactions/{transaction_id}/payments/paypal"
            response = requests.post(url, headers=self.headers, cookies=self.cookies)
            
            if response.status_code == 200:
                payment_data = response.json()
                paypal_url = payment_data.get('redirect_url') or payment_data.get('payment_url')
                
                if paypal_url:
                    logging.info(f"✅ PayPal URL obtained: {paypal_url[:50]}...")
                    return paypal_url
                else:
                    logging.error(f"❌ No PayPal URL in response: {payment_data}")
                    return None
            else:
                logging.error(f"❌ Failed to get PayPal URL: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error getting PayPal URL: {e}")
            return None
    
    def reserve_item(self, item_id: str, item_title: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        ГЛАВНАЯ ФУНКЦИЯ: Резервирование товара и получение PayPal ссылки
        
        Returns:
            (success: bool, paypal_url: str, reservation_id: str)
        """
        try:
            logging.info(f"🎯 Starting reservation for item {item_id}: {item_title}")
            
            # 1. Получаем детали товара
            item_details = self.get_item_details(item_id)
            if not item_details:
                return False, None, None
            
            # Проверяем, что товар доступен для покупки
            if not item_details.get('can_be_sold', False):
                logging.warning(f"⚠️ Item {item_id} cannot be sold")
                return False, None, None
            
            # 2. Получаем опции доставки
            shipping_options = self.get_shipping_options(item_id)
            if not shipping_options or not shipping_options.get('shipping_options'):
                logging.error(f"❌ No shipping options for item {item_id}")
                return False, None, None
            
            # Выбираем самую дешевую доставку
            cheapest_shipping = min(
                shipping_options['shipping_options'], 
                key=lambda x: float(x.get('price', '999'))
            )
            shipping_id = cheapest_shipping['id']
            
            logging.info(f"📦 Selected shipping: {cheapest_shipping.get('provider')} - {cheapest_shipping.get('price')}€")
            
            # 3. Создаем checkout сессию (резервируем товар)
            transaction = self.create_checkout_session(item_id, shipping_id)
            if not transaction:
                return False, None, None
            
            transaction_id = transaction['id']
            
            # Небольшая задержка для обработки на стороне Vinted
            time.sleep(2)
            
            # 4. Получаем PayPal ссылку для оплаты
            paypal_url = self.get_paypal_payment_url(transaction_id)
            if not paypal_url:
                logging.error(f"❌ Failed to get PayPal URL for transaction {transaction_id}")
                return False, None, transaction_id
            
            # 5. Сохраняем информацию о резервации
            reservation_info = {
                'item_id': item_id,
                'item_title': item_title,
                'transaction_id': transaction_id,
                'paypal_url': paypal_url,
                'reserved_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=15),
                'shipping_cost': cheapest_shipping.get('price', '0'),
                'item_price': item_details.get('price', '0')
            }
            
            self.reservations[transaction_id] = reservation_info
            
            logging.info(f"🎉 RESERVATION SUCCESS!")
            logging.info(f"📍 Transaction ID: {transaction_id}")
            logging.info(f"💰 Item: {item_title}")
            logging.info(f"🔗 PayPal URL: {paypal_url[:80]}...")
            logging.info(f"⏰ Expires: {reservation_info['expires_at'].strftime('%H:%M:%S')}")
            
            return True, paypal_url, transaction_id
            
        except Exception as e:
            logging.error(f"❌ Critical error in reserve_item: {e}")
            return False, None, None
    
    def get_active_reservations(self) -> Dict:
        """Получение списка активных резерваций"""
        now = datetime.now()
        active = {}
        
        for res_id, info in self.reservations.items():
            if info['expires_at'] > now:
                active[res_id] = info
            else:
                logging.info(f"⏰ Reservation {res_id} expired")
        
        # Удаляем истекшие резервации
        self.reservations = active
        return active
    
    def cancel_reservation(self, transaction_id: str) -> bool:
        """Отмена резервации (если возможно)"""
        try:
            url = f"https://www.vinted.it/api/v2/transactions/{transaction_id}/cancel"
            response = requests.post(url, headers=self.headers, cookies=self.cookies)
            
            if response.status_code == 200:
                logging.info(f"✅ Reservation {transaction_id} cancelled")
                if transaction_id in self.reservations:
                    del self.reservations[transaction_id]
                return True
            else:
                logging.error(f"❌ Failed to cancel reservation: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error cancelling reservation: {e}")
            return False
