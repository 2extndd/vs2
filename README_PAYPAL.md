# 🎯 PayPal Auto-Reservation - Quick Start

## 💡 РЕШЕНИЕ ПРОБЛЕМЫ РАЗНЫХ АККАУНТОВ

### Проблема:
- **Бот-аккаунт** резервирует → **Личный аккаунт** должен оплатить

### Решение:
```
1. 🤖 Бот создает резервацию на Vinted
2. 🔗 Получает универсальную PayPal ссылку  
3. 📱 Отправляет ссылку в Telegram
4. 💳 Вы оплачиваете со СВОЕГО PayPal аккаунта
```

## 🚀 БЫСТРЫЙ ЗАПУСК

### 1. Активация ветки:
```bash
git checkout feature/paypal-reservation
```

### 2. Настройка Config.py:
```python
# PayPal Auto-Reservation
paypal_reservation_enabled = True
reservation_topics = ["bags", "bags 2"] 
max_reservations_per_hour = 5
min_reservation_price = 10
max_reservation_price = 500
```

### 3. Результат в Telegram:
```
🎯 ТОВАР ЗАРЕЗЕРВИРОВАН!

📦 Chanel Vintage Bag
💰 Цена: 150€
⏰ Истекает в 14:45:30 (15 минут)

🔗 ОПЛАТИТЬ ЧЕРЕЗ PAYPAL
(универсальная ссылка)

💡 Нажмите → Войдите в СВОЙ PayPal → Оплатите
```

## 📊 НОВЫЕ КОМАНДЫ

- `/reservations` - активные резервации
- `/cancel TXN-123` - отмена резервации

## ⚠️ ВАЖНО

- 🧪 **ЭКСПЕРИМЕНТАЛЬНАЯ ФУНКЦИЯ!**
- 💰 Тестируйте на дешевых товарах
- 🕒 Резервация = 15 минут
- 📈 Лимит: 5 резерваций/час

## 📖 Полная документация: 
`PAYPAL_RESERVATION_GUIDE.md`
