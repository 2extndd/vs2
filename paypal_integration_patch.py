#!/usr/bin/env python3
"""
🔧 Патч для интеграции PayPal резервирования в основной vinted_scanner.py

Этот файл содержит код для добавления в vinted_scanner.py
"""

# ===== ДОБАВИТЬ В ИМПОРТЫ =====
"""
from vinted_paypal_reservation import VintedPayPalReservation, format_reservation_message
"""

# ===== ДОБАВИТЬ В ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
"""
# PayPal Reservation System
paypal_reservation = None
reservation_count_hour = 0
last_reservation_hour = datetime.now().hour
"""

# ===== ДОБАВИТЬ ФУНКЦИИ =====

def init_paypal_reservation():
    """Инициализация системы PayPal резервирования"""
    global paypal_reservation
    
    try:
        if Config.paypal_reservation_enabled:
            # Получаем cookies от основной сессии
            session = requests.Session()
            session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
            cookies = session.cookies.get_dict()
            
            # Инициализируем систему резервирования
            user_agent = headers.get("User-Agent", "Mozilla/5.0")
            paypal_reservation = VintedPayPalReservation(cookies, user_agent)
            
            logging.info("✅ PayPal Reservation System initialized")
        else:
            logging.info("⏸️ PayPal Reservation disabled in config")
            
    except Exception as e:
        logging.error(f"❌ Failed to initialize PayPal Reservation: {e}")
        paypal_reservation = None

def should_reserve_item(item_id: str, topic_name: str, item_price: str) -> bool:
    """Проверка, нужно ли резервировать товар"""
    global reservation_count_hour, last_reservation_hour
    
    try:
        # Проверяем, включено ли резервирование
        if not Config.paypal_reservation_enabled or not paypal_reservation:
            return False
        
        # Проверяем, что топик в списке для резервирования
        if topic_name not in Config.reservation_topics:
            return False
        
        # Сброс счетчика резерваций каждый час
        current_hour = datetime.now().hour
        if current_hour != last_reservation_hour:
            reservation_count_hour = 0
            last_reservation_hour = current_hour
        
        # Проверяем лимит резерваций в час
        if reservation_count_hour >= Config.max_reservations_per_hour:
            logging.warning(f"⏰ Reservation limit reached: {reservation_count_hour}/{Config.max_reservations_per_hour}")
            return False
        
        # Проверяем цену товара
        try:
            price_value = float(item_price.split()[0])  # Извлекаем числовое значение
            if price_value < Config.min_reservation_price or price_value > Config.max_reservation_price:
                logging.info(f"💰 Item price {price_value}€ outside reservation range {Config.min_reservation_price}-{Config.max_reservation_price}€")
                return False
        except (ValueError, IndexError):
            logging.warning(f"⚠️ Cannot parse item price: {item_price}")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error in should_reserve_item: {e}")
        return False

def send_telegram_reservation_message(message: str, thread_id: str = None):
    """Отправка сообщения о резервации в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
        
        params = {
            "chat_id": Config.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False  # Показываем превью для PayPal ссылок
        }
        
        # Отправляем в тот же топик, если указан
        if thread_id:
            params["message_thread_id"] = thread_id
        
        response = requests.post(url, data=params, timeout=timeoutconnection)
        
        if response.status_code == 200:
            logging.info("✅ Reservation message sent to Telegram")
            return True
        else:
            logging.error(f"❌ Failed to send reservation message: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error sending reservation message: {e}")
        return False

# ===== МОДИФИКАЦИЯ send_telegram_message =====
def enhanced_send_telegram_message(item_title, item_price, item_url, item_image, item_size=None, thread_id=None, item_id=None, topic_name=None):
    """Улучшенная функция отправки с резервированием"""
    global reservation_count_hour
    
    # Отправляем обычное сообщение
    success = send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id)
    
    # Если основное сообщение отправлено И включено резервирование
    if success and should_reserve_item(item_id, topic_name, item_price):
        try:
            logging.info(f"🎯 ATTEMPTING RESERVATION: {item_title}")
            
            # Пытаемся зарезервировать товар
            reserved, paypal_url, res_id = paypal_reservation.reserve_item(item_id, item_title)
            
            if reserved and paypal_url:
                # Увеличиваем счетчик резерваций
                reservation_count_hour += 1
                
                # Создаем сообщение о резервации
                expires_at = datetime.now() + timedelta(minutes=15)
                reservation_msg = format_reservation_message(
                    True, paypal_url, res_id, item_title, item_price, expires_at
                )
                
                # Отправляем сообщение о резервации
                send_telegram_reservation_message(reservation_msg, thread_id)
                
                logging.info(f"🎉 RESERVATION SUCCESSFUL: {item_title}")
                logging.info(f"📊 Reservations today: {reservation_count_hour}/{Config.max_reservations_per_hour}")
                
                # Задержка после резервирования
                time.sleep(3)
                
            else:
                logging.warning(f"❌ RESERVATION FAILED: {item_title}")
                
        except Exception as e:
            logging.error(f"❌ Reservation error for {item_title}: {e}")
    
    return success

# ===== НОВЫЕ КОМАНДЫ БОТА =====

async def reservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reservations - показать активные резервации"""
    try:
        if not paypal_reservation:
            await update.message.reply_text("❌ PayPal резервирование отключено")
            return
        
        active_reservations = paypal_reservation.get_active_reservations()
        
        if not active_reservations:
            await update.message.reply_text("📭 Нет активных резерваций")
            return
        
        message = "🎯 <b>АКТИВНЫЕ РЕЗЕРВАЦИИ:</b>\n\n"
        
        for res_id, info in active_reservations.items():
            expires_in = info['expires_at'] - datetime.now()
            minutes_left = int(expires_in.total_seconds() / 60)
            
            message += f"📦 <b>{info['item_title'][:30]}...</b>\n"
            message += f"💰 {info['item_price']}\n"
            message += f"🆔 <code>{res_id}</code>\n"
            message += f"⏰ Осталось: <b>{minutes_left} мин</b>\n"
            message += f"🔗 <a href=\"{info['paypal_url']}\">Оплатить</a>\n\n"
        
        message += f"📊 Резерваций за час: {reservation_count_hour}/{Config.max_reservations_per_hour}"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def cancel_reservation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel - отмена резервации"""
    try:
        if not context.args:
            await update.message.reply_text("❌ Укажите ID резервации: /cancel TXN-123456")
            return
        
        reservation_id = context.args[0]
        
        if not paypal_reservation:
            await update.message.reply_text("❌ PayPal резервирование отключено")
            return
        
        success = paypal_reservation.cancel_reservation(reservation_id)
        
        if success:
            await update.message.reply_text(f"✅ Резервация {reservation_id} отменена")
        else:
            await update.message.reply_text(f"❌ Не удалось отменить резервацию {reservation_id}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# ===== МОДИФИКАЦИЯ setup_bot =====
"""
# В функции setup_bot() добавить:
application.add_handler(CommandHandler("reservations", reservations_command))
application.add_handler(CommandHandler("cancel", cancel_reservation_command))
"""

# ===== МОДИФИКАЦИЯ main() =====
"""
# В функции main() после load_analyzed_item() добавить:
init_paypal_reservation()

# В scanner_loop() заменить вызов send_telegram_message на:
enhanced_send_telegram_message(item_title, item_price, item_url, item_image, item_size, thread_id, item_id, topic_name)
"""

if __name__ == "__main__":
    print("�� PayPal Integration Patch for VintedScanner")
    print("Apply this code to vinted_scanner.py to enable PayPal auto-reservation")
