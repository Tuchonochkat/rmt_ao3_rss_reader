#!/usr/bin/env python3
"""
Скрипт для тестирования бота
Запускает одну проверку RSS ленты и отправляет результаты в Telegram
"""

import asyncio
import logging

from bot import RSSBot

# Настройка логирования для тестирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_bot():
    """Тестирует работу бота"""
    try:
        logger.info("=== ТЕСТИРОВАНИЕ RSS BOT ===")

        # Создаем экземпляр бота
        bot = RSSBot()

        # Тестируем соединение
        logger.info("1. Тестирование соединения с Telegram...")
        if not await bot.test_connection():
            logger.error("❌ Не удалось подключиться к Telegram")
            return False
        logger.info("✅ Соединение с Telegram установлено")

        # Отправляем тестовое сообщение
        logger.info("2. Отправка тестового сообщения...")
        if await bot.send_test_message():
            logger.info("✅ Тестовое сообщение отправлено")
        else:
            logger.error("❌ Не удалось отправить тестовое сообщение")
            return False

        # Проверяем RSS ленту
        logger.info("3. Проверка RSS ленты...")
        await bot.run_once()
        logger.info("✅ Проверка RSS ленты завершена")

        logger.info("=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ===")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bot())
    exit(0 if success else 1)
