#!/usr/bin/env python3
"""
Скрипт для запуска бота в продакшене
"""

import asyncio
import logging
import signal
import sys

from telegram_bot.bot import RSSBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class BotRunner:
    """Класс для управления запуском бота"""

    def __init__(self):
        self.bot = None
        self.running = False

    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.running = False
        sys.exit(0)

    async def start(self):
        """Запускает бота"""
        try:
            logger.info("=== ЗАПУСК RSS BOT ===")

            # Создаем экземпляр бота
            self.bot = RSSBot()
            self.running = True

            # Настраиваем обработчики сигналов
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Запускаем бота
            logger.info("Запуск бота...")
            await self.bot.start()

        except Exception as e:
            logger.error(f"Критическая ошибка при запуске: {e}")
            return False


def main():
    """Основная функция"""
    runner = BotRunner()

    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
