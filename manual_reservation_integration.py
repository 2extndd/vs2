#!/usr/bin/env python3
"""
🔧 Интеграция ручного PayPal резервирования в vinted_scanner.py

ИЗМЕНЕНИЯ В ОСНОВНОМ БОТЕ:
1. Добавить кнопки к сообщениям с товарами
2. Добавить обработчики кнопок и команд
3. Добавить команду /reserve
"""

# ===== ДОБАВИТЬ В ИМПОРТЫ =====
"""
from vinted_manual_reservation import (
    VintedManualReservation, 
    create_reservation_keyboard,
    format_item_message_with_button,
    handle_reservation_button,
    reserve_command,
    manual_reservation_system
)
from telegram.ext import CallbackQueryHandler
"""

# ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
"""
# Manual reservation system
manual_reservation_system = None
manual_reservation_count = 0
last_reservation_hour = datetime.now().hour
"""

# ===== НОВЫЕ ФУНКЦИИ =====

def init_manual_reservation():
    """Инициализация системы ручного резервирования"""
    global manual_reservation_system
    
    try:
        if hasattr(Config, 'paypal_manual_reservation_enabled') and Config.paypal_manual_reservation_enabled:
            # Получаем cookies от основной сессии
            session = requests.Session()
            session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
            cookies = session.cookies.get_dict()
            
            # Инициализируем систему резервирования
            user_agent = headers.get("User-Agent", "Mozilla/5.0")
            manual_reservation_system = VintedManualReservation(cookies, user_agent)
            
            logging.info("✅ Manual PayPal Reservation System initialized")
        else:
            logging.info("⏸️ Manual PayPal Reservation disabled in config")
            
    except Exception as e:
        logging.error(f"❌ Failed to initialize Manual Reservation: {e}")
        manual_reservation_system = None

def should_show_reservation_button(topic_name: str, item_price: str) -> bool:
    """Проверка, нужно ли показывать кнопку резервирования"""
    try:
        # Проверяем конфигурацию
        if not hasattr(Config, 'paypal_manual_reservation_enabled') or not Config.paypal_manual_reservation_enabled:
            return False
        
        if not manual_reservation_system:
            return False
        
        # Проверяем топик
        if hasattr(Config, 'reservation_button_topics'):
            if topic_name not in Config.reservation_button_topics:
                return False
        
        # Проверяем цену
        if hasattr(Config, 'min_reservation_price') and hasattr(Config, 'max_reservation_price'):
            try:
                price_value = float(item_price.split()[0])
                if price_value < Config.min_reservation_price or price_value > Config.max_reservation_price:
                    return False
            except (ValueError, IndexError):
                return False
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error in should_show_reservation_button: {e}")
        return False

def check_reservation_limits() -> bool:
    """Проверка лимитов резервирования"""
    global manual_reservation_count, last_reservation_hour
    
    try:
        # Сброс счетчика каждый час
        current_hour = datetime.now().hour
        if current_hour != last_reservation_hour:
            manual_reservation_count = 0
            last_reservation_hour = current_hour
        
        # Проверяем лимит
        max_limit = getattr(Config, 'max_manual_reservations_per_hour', 10)
        return manual_reservation_count < max_limit
        
    except Exception as e:
        logging.error(f"❌ Error checking reservation limits: {e}")
        return False

# ===== МОДИФИКАЦИЯ send_telegram_message =====
def enhanced_send_telegram_message_with_buttons(item_title, item_price, item_url, item_image, 
                                               item_size=None, thread_id=None, item_id=None, topic_name=None):
    """Улучшенная функция отправки с кнопками резервирования"""
    
    try:
        # Определяем, нужна ли кнопка резервирования
        show_button = should_show_reservation_button(topic_name, item_price)
        
        if show_button and item_id:
            # Сохраняем данные товара для резервирования
            if manual_reservation_system:
                item_data = {
                    'title': item_title,
                    'price': item_price,
                    'url': item_url,
                    'image': item_image,
                    'size': item_size
                }
                manual_reservation_system.store_item_for_reservation(item_id, item_data)
            
            # Создаем сообщение с кнопкой
            size_text = f"\n👕 Размер: {item_size}" if item_size else ""
            topic_text = f"\n🏷️ Топик: {topic_name}" if topic_name else ""
            
            message = f"<b>{item_title}</b>\n🏷️ {item_price}{size_text}{topic_text}\n🔗 {item_url}"
            
            # Создаем клавиатуру с кнопкой
            keyboard = create_reservation_keyboard(item_id)
            
            # Отправляем в топик с кнопкой
            if thread_id:
                params_topic = {
                    "chat_id": Config.telegram_chat_id,
                    "photo": item_image,
                    "caption": message,
                    "parse_mode": "HTML",
                    "message_thread_id": thread_id,
                    "reply_markup": keyboard.to_json()
                }
                
                url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
                response = requests.post(url, data=params_topic, timeout=timeoutconnection)
                
                if response.status_code == 200:
                    logging.info(f"✅ Message with reservation button sent to topic {thread_id}")
                    return True
            
            # Fallback: отправляем в основной чат с кнопкой
            params_main = {
                "chat_id": Config.telegram_chat_id,
                "photo": item_image,
                "caption": message + "\n⚠️ Отправлено в основной чат",
                "parse_mode": "HTML",
                "reply_markup": keyboard.to_json()
            }
            
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
            response = requests.post(url, data=params_main, timeout=timeoutconnection)
            
            if response.status_code == 200:
                logging.info(f"✅ Message with reservation button sent to main chat")
                return True
            else:
                # Если не удалось с кнопкой, отправляем обычное сообщение
                return send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
        
        else:
            # Отправляем обычное сообщение без кнопки
            return send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
            
    except Exception as e:
        logging.error(f"❌ Error in enhanced_send_telegram_message_with_buttons: {e}")
        # Fallback: обычное сообщение
        return send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)

# ===== НОВЫЕ КОМАНДЫ БОТА =====

async def manual_reservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reservations - показать активные ручные резервации"""
    try:
        if not manual_reservation_system:
            await update.message.reply_text("❌ Система ручного резервирования отключена")
            return
        
        active_reservations = manual_reservation_system.active_reservations
        
        if not active_reservations:
            await update.message.reply_text("📭 Нет активных резерваций")
            return
        
        message = "🎯 <b>АКТИВНЫЕ РУЧНЫЕ РЕЗЕРВАЦИИ:</b>\n\n"
        
        for res_id, info in active_reservations.items():
            expires_in = info['expires_at'] - datetime.now()
            minutes_left = max(0, int(expires_in.total_seconds() / 60))
            
            if minutes_left > 0:
                message += f"📦 <b>{info['item_title'][:30]}...</b>\n"
                message += f"💰 {info.get('item_price', 'N/A')}\n"
                message += f"🆔 <code>{res_id}</code>\n"
                message += f"⏰ Осталось: <b>{minutes_left} мин</b>\n"
                message += f"🔗 <a href=\"{info['paypal_url']}\">Оплатить</a>\n\n"
        
        message += f"📊 Резерваций за час: {manual_reservation_count}/{getattr(Config, 'max_manual_reservations_per_hour', 10)}"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# ===== МОДИФИКАЦИЯ setup_bot =====
"""
# В функции setup_bot() добавить:
application.add_handler(CommandHandler("reservations", manual_reservations_command))
application.add_handler(CommandHandler("reserve", reserve_command))
application.add_handler(CallbackQueryHandler(handle_reservation_button, pattern="^reserve_"))
"""

# ===== МОДИФИКАЦИЯ main() =====
"""
# В функции main() после load_analyzed_item() добавить:
init_manual_reservation()

# В scanner_loop() заменить вызов send_telegram_message на:
enhanced_send_telegram_message_with_buttons(item_title, item_price, item_url, item_image, item_size, thread_id, item_id, topic_name)
"""

if __name__ == "__main__":
    print("🔧 Manual PayPal Reservation Integration for VintedScanner")
    print("Apply this code to vinted_scanner.py to enable manual PayPal reservation with buttons")
