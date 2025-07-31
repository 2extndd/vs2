#!/usr/bin/env python3
"""
Тест переключения режимов /fast и /slow
"""

import sys
sys.path.append('.')

import vinted_scanner
import asyncio
from unittest.mock import Mock, AsyncMock

async def test_mode_switching():
    """Тестирование переключения режимов"""
    print("🧪 Тестирование переключения режимов...")
    
    # Создаем мок объекты
    mock_update = Mock()
    mock_context = Mock()
    mock_message = Mock()
    mock_message.reply_text = AsyncMock()  # AsyncMock для async функций
    mock_update.message = mock_message
    
    # Тестируем начальное состояние
    print(f"📊 Начальный режим: {vinted_scanner.scan_mode}")
    
    # Тестируем команду /fast
    print("\n🐰 Тестирование /fast...")
    await vinted_scanner.fast_command(mock_update, mock_context)
    print(f"✅ Режим после /fast: {vinted_scanner.scan_mode}")
    mock_message.reply_text.assert_called_with("🐰 FAST mode: 5-7s priority, 10-15s normal")
    
    # Тестируем команду /slow
    print("\n🐌 Тестирование /slow...")
    await vinted_scanner.slow_command(mock_update, mock_context)
    print(f"✅ Режим после /slow: {vinted_scanner.scan_mode}")
    mock_message.reply_text.assert_called_with("🐌 SLOW mode: 25-35s priority, 45-60s normal")
    
    # Тестируем команду /mode
    print("\n📊 Тестирование /mode...")
    await vinted_scanner.mode_command(mock_update, mock_context)
    
    print("\n✅ Все команды работают корректно!")
    print(f"📊 Финальный режим: {vinted_scanner.scan_mode}")

if __name__ == "__main__":
    asyncio.run(test_mode_switching()) 