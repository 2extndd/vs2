#!/usr/bin/env python3
"""
🎯 VintedScanner Manual PayPal Reservation Module

РУЧНОЕ резервирование товаров через PayPal по команде/кнопке на 15 минут
с последующей передачей ссылки для оплаты на другом аккаунте.

ИСПОЛЬЗОВАНИЕ:
1. Бот отправляет товар с кнопкой "💳 Зарезервировать"
2. Пользователь нажимает кнопку ИЛИ отвечает командой /reserve
3. Бот резервирует товар и отправляет PayPal ссылку
4. Пользователь оплачивает со своего PayPal аккаунта
"""

import time
import json
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler

class VintedManualReservation:
    """Класс для ручного резервирования товаров через PayPal"""
    
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
        self.active_reservations = {}  # Хранение активных резерваций
        self.pending_items = {}        # Товары, ожидающие резервирования
        
    def extract_item_id_from_url(self, item_url: str) -> Optional[str]:
        """Извлечение ID товара из Vinted URL"""
        try:
            # URL формат: https://www.vinted.it/items/3785692-chanel-bag
            if '/items/' in item_url:
                item_part = item_url.split('/items/')[1]
                item_id = item_part.split('-')[0]
                return item_id
            return None
        except:
            return None
    
    def store_item_for_reservation(self, item_id: str, item_data: dict):
        """Сохранение данных товара для последующего резервирования"""
        self.pending_items[item_id] = {
            'title': item_data.get('title', 'Unknown'),
            'price': item_data.get('price', '0€'),
            'url': item_data.get('url', ''),
            'image': item_data.get('image', ''),
            'size': item_data.get('size'),
            'stored_at': datetime.now()
        }
        
        # Удаляем старые товары (старше 1 часа)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.pending_items = {
            k: v for k, v in self.pending_items.items() 
            if v['stored_at'] > cutoff_time
        }
    
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
            checkout_data = {
                "item_id": int(item_id),
                "shipping_option_id": int(shipping_option_id),
                "payment_method": "paypal",
                "message": "Reserved via VintedScanner bot",
            }
            
            url = "https://www.vinted.it/api/v2/transactions"
            response = requests.post(
                url, 
                headers=self.headers, 
                cookies=self.cookies,
                json=checkout_data
            )
            
            if response.status_code == 201:
                transaction = response.json()
                logging.info(f"✅ Manual reservation created: {transaction.get('id')}")
                return transaction
            else:
                logging.error(f"❌ Failed to create reservation: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error creating reservation: {e}")
            return None
    
    def get_paypal_payment_url(self, transaction_id: str) -> Optional[str]:
        """Получение ссылки для оплаты через PayPal"""
        try:
            url = f"https://www.vinted.it/api/v2/transactions/{transaction_id}/payments/paypal"
            response = requests.post(url, headers=self.headers, cookies=self.cookies)
            
            if response.status_code == 200:
                payment_data = response.json()
                paypal_url = payment_data.get('redirect_url') or payment_data.get('payment_url')
                
                if paypal_url:
                    logging.info(f"✅ PayPal URL obtained for manual reservation")
                    return paypal_url
                else:
                    logging.error(f"❌ No PayPal URL in response: {payment_data}")
                    return None
            else:
                logging.error(f"❌ Failed to get PayPal URL: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error getting PayPal URL: {e}")
            return None
    
    def reserve_item_manually(self, item_id: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        РУЧНОЕ резервирование товара по запросу пользователя
        
        Returns:
            (success: bool, paypal_url: str, reservation_id: str, item_title: str)
        """
        try:
            logging.info(f"🎯 Manual reservation requested for item {item_id}")
            
            # Пытаемся получить данные из кэша
            item_data = self.pending_items.get(item_id)
            item_title = item_data['title'] if item_data else "Unknown Item"
            
            # Получаем детали товара
            item_details = self.get_item_details(item_id)
            if not item_details:
                return False, None, None, item_title
            
            # Обновляем title из API
            item_title = item_details.get('title', item_title)
            
            # Проверяем доступность
            if not item_details.get('can_be_sold', False):
                logging.warning(f"⚠️ Item {item_id} cannot be sold")
                return False, None, None, item_title
            
            # Получаем опции доставки
            shipping_options = self.get_shipping_options(item_id)
            if not shipping_options or not shipping_options.get('shipping_options'):
                logging.error(f"❌ No shipping options for item {item_id}")
                return False, None, None, item_title
            
            # Выбираем самую дешевую доставку
            cheapest_shipping = min(
                shipping_options['shipping_options'], 
                key=lambda x: float(x.get('price', '999'))
            )
            shipping_id = cheapest_shipping['id']
            
            # Создаем резервацию
            transaction = self.create_checkout_session(item_id, shipping_id)
            if not transaction:
                return False, None, None, item_title
            
            transaction_id = transaction['id']
            time.sleep(2)  # Задержка для обработки
            
            # Получаем PayPal ссылку
            paypal_url = self.get_paypal_payment_url(transaction_id)
            if not paypal_url:
                return False, None, transaction_id, item_title
            
            # Сохраняем резервацию
            reservation_info = {
                'item_id': item_id,
                'item_title': item_title,
                'transaction_id': transaction_id,
                'paypal_url': paypal_url,
                'reserved_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=15),
                'shipping_cost': cheapest_shipping.get('price', '0'),
                'item_price': item_details.get('price', '0'),
                'reserved_by': 'manual'
            }
            
            self.active_reservations[transaction_id] = reservation_info
            
            logging.info(f"🎉 MANUAL RESERVATION SUCCESS: {item_title}")
            
            return True, paypal_url, transaction_id, item_title
            
        except Exception as e:
            logging.error(f"❌ Manual reservation error: {e}")
            return False, None, None, item_title if 'item_title' in locals() else "Unknown"


def create_reservation_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Создание клавиатуры с кнопкой резервирования"""
    keyboard = [
        [InlineKeyboardButton("💳 Зарезервировать", callback_data=f"reserve_{item_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def format_item_message_with_button(item_title: str, item_price: str, item_url: str, 
                                  item_size: str = None, topic_name: str = None) -> str:
    """Форматирование сообщения с товаром и кнопкой резервирования"""
    
    size_text = f"\n👕 Размер: {item_size}" if item_size else ""
    topic_text = f"\n🏷️ Топик: {topic_name}" if topic_name else ""
    
    message = f"""<b>{item_title}</b>
🏷️ {item_price}{size_text}{topic_text}
🔗 {item_url}

💡 <i>Нажмите кнопку ниже для резервирования товара</i>"""
    
    return message


def format_reservation_success_message(item_title: str, item_price: str, paypal_url: str, 
                                     reservation_id: str, expires_at: datetime) -> str:
    """Форматирование сообщения об успешном резервировании"""
    
    message = f"""🎯 <b>ТОВАР ЗАРЕЗЕРВИРОВАН!</b>

📦 <b>{item_title}</b>
💰 Цена: <b>{item_price}</b>
🆔 ID: <code>{reservation_id}</code>

⏰ <b>ВНИМАНИЕ:</b> Резервация истекает в <b>{expires_at.strftime('%H:%M:%S')}</b> (15 минут)

🔗 <b>ССЫЛКА ДЛЯ ОПЛАТЫ:</b>
<a href="{paypal_url}">💳 ОПЛАТИТЬ ЧЕРЕЗ PAYPAL</a>

💡 <b>Инструкция:</b>
1. Нажмите на ссылку выше
2. Войдите в СВОЙ PayPal аккаунт  
3. Подтвердите оплату
4. Товар будет ваш!

⚠️ <b>Важно:</b> Ссылка работает с любого PayPal аккаунта!"""
    
    return message


def format_reservation_error_message(item_title: str, error_reason: str = None) -> str:
    """Форматирование сообщения об ошибке резервирования"""
    
    reason_text = f"\n📋 Причина: {error_reason}" if error_reason else ""
    
    message = f"""❌ <b>ОШИБКА РЕЗЕРВАЦИИ</b>

📦 {item_title}{reason_text}

🔄 Попробуйте еще раз через несколько минут
💡 Возможно товар уже продан или недоступен"""
    
    return message


# Обработчики для Telegram бота
async def handle_reservation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопки резервирования"""
    global manual_reservation_system
    
    query = update.callback_query
    await query.answer()
    
    try:
        # Извлекаем item_id из callback_data
        if not query.data.startswith('reserve_'):
            return
        
        item_id = query.data.replace('reserve_', '')
        
        if not manual_reservation_system:
            await query.edit_message_text("❌ Система резервирования недоступна")
            return
        
        # Показываем прогресс
        await query.edit_message_text("🔄 Резервирую товар...")
        
        # Выполняем резервирование
        success, paypal_url, reservation_id, item_title = manual_reservation_system.reserve_item_manually(item_id)
        
        if success and paypal_url:
            expires_at = datetime.now() + timedelta(minutes=15)
            success_msg = format_reservation_success_message(
                item_title, "см. выше", paypal_url, reservation_id, expires_at
            )
            await query.edit_message_text(success_msg, parse_mode="HTML")
        else:
            error_msg = format_reservation_error_message(item_title)
            await query.edit_message_text(error_msg, parse_mode="HTML")
            
    except Exception as e:
        logging.error(f"❌ Error in reservation button handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при резервировании")


async def reserve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reserve как ответ на сообщение с товаром"""
    global manual_reservation_system
    
    try:
        # Проверяем, что команда отправлена как ответ
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Отправьте /reserve как ответ на сообщение с товаром")
            return
        
        if not manual_reservation_system:
            await update.message.reply_text("❌ Система резервирования недоступна")
            return
        
        # Извлекаем URL из сообщения
        original_message = update.message.reply_to_message.text or update.message.reply_to_message.caption
        
        if not original_message or 'vinted.it/items/' not in original_message:
            await update.message.reply_text("❌ В сообщении не найдена ссылка на товар Vinted")
            return
        
        # Извлекаем item_id из URL
        import re
        url_match = re.search(r'https://www\.vinted\.it/items/(\d+)', original_message)
        
        if not url_match:
            await update.message.reply_text("❌ Не удалось извлечь ID товара из ссылки")
            return
        
        item_id = url_match.group(1)
        
        # Отправляем уведомление о начале резервирования
        progress_msg = await update.message.reply_text("🔄 Резервирую товар...")
        
        # Выполняем резервирование
        success, paypal_url, reservation_id, item_title = manual_reservation_system.reserve_item_manually(item_id)
        
        if success and paypal_url:
            expires_at = datetime.now() + timedelta(minutes=15)
            success_msg = format_reservation_success_message(
                item_title, "см. выше", paypal_url, reservation_id, expires_at
            )
            await progress_msg.edit_text(success_msg, parse_mode="HTML")
        else:
            error_msg = format_reservation_error_message(item_title)
            await progress_msg.edit_text(error_msg, parse_mode="HTML")
            
    except Exception as e:
        logging.error(f"❌ Error in reserve command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при резервировании")


# Глобальная переменная для системы резервирования
manual_reservation_system = None


if __name__ == "__main__":
    print("🧪 VintedManual Reservation Module - Manual Mode")
    print("This module provides MANUAL PayPal reservation for Vinted items")
    print("Integration required with main vinted_scanner.py")
