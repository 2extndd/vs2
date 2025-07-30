# New status command with error counts
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    global bot_running, scan_mode, last_errors
    status = "🟢 Бот работает" if bot_running else "🔴 Бот остановлен"
    items_count = len(list_analyzed_items)
    
    # Scan mode info
    mode_emoji = "🐰" if scan_mode == "fast" else "🐌"
    mode_interval = "30 сек" if scan_mode == "fast" else "120 сек"
    mode_info = f"\n{mode_emoji} Режим: {scan_mode} (интервал: {mode_interval})"
    
    # Count errors by type
    vinted_errors = len([e for e in last_errors if "Vinted" in e])
    telegram_errors = len([e for e in last_errors if "TG" in e or "Telegram" in e])
    email_errors = len([e for e in last_errors if "Email" in e])
    slack_errors = len([e for e in last_errors if "Slack" in e])
    scanner_errors = len([e for e in last_errors if "Scanner" in e])
    
    # Error summary
    error_info = ""
    if last_errors:
        error_info = f"\n❌ Последние ошибки:"
        if vinted_errors > 0:
            error_info += f"\nVinted ({vinted_errors} ошибок)"
        if telegram_errors > 0:
            error_info += f"\nTelegram ({telegram_errors} ошибок)"
        if email_errors > 0:
            error_info += f"\nEmail ({email_errors} ошибок)"
        if slack_errors > 0:
            error_info += f"\nSlack ({slack_errors} ошибок)"
        if scanner_errors > 0:
            error_info += f"\nScanner ({scanner_errors} ошибок)"
    
    response = f"{status}\n📊 Проанализировано товаров: {items_count}{mode_info}{error_info}"
    await update.message.reply_text(response)
