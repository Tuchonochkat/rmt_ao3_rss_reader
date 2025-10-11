#!/usr/bin/env python3
"""
Скрипт для тестирования бота
Тестирует соединение с Telegram и обработку очереди Redis
"""

import asyncio
import logging
import sys

from telegram_bot.bot import RSSBot

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

        # Тестируем соединение с Telegram
        logger.info("1. Тестирование соединения с Telegram...")
        if not await bot.telegram_notifier.test_connection():
            logger.error("❌ Не удалось подключиться к Telegram")
            return False
        logger.info("✅ Соединение с Telegram установлено")

        # Тестируем соединение с Redis
        logger.info("2. Тестирование соединения с Redis...")
        await bot.redis.connect()
        logger.info("✅ Соединение с Redis установлено")

        # Проверяем очередь
        logger.info("3. Проверка очереди Redis...")
        queue_length = await bot.redis.get_queue_length()
        logger.info(f"✅ В очереди {queue_length} элементов")

        # Тестируем обработку одного элемента (если есть)
        if queue_length > 0:
            logger.info("4. Тестирование обработки элемента из очереди...")
            processed = await bot.process_queue()
            logger.info(f"✅ Обработано {processed} элементов")
        else:
            logger.info("4. Очередь пуста, пропускаем тест обработки")

        logger.info("=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ===")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False


async def main():
    """Главная функция"""
    success = await test_bot()
    return 0 if success else 1


def cli_main():
    """Точка входа для CLI"""
    try:
        exit_code = asyncio.run(main())
        return exit_code
    except KeyboardInterrupt:
        print("Программа прервана пользователем")
        return 0
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
