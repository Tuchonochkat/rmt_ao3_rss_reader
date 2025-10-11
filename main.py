#!/usr/bin/env python3
"""
Главный файл для запуска полной системы:
- RSS парсер: проверяет RSS ленты и добавляет новые записи в очередь Redis
- Telegram бот: обрабатывает очередь и отправляет сообщения в канал
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from config import Config
from rss_parser.rss_parser import RSSParser
from telegram_bot.bot import RSSBot

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class RSSParserService:
    """Сервис для периодической проверки RSS лент"""

    def __init__(self):
        self.rss_parser = None
        self.running = False
        self.task = None

    async def initialize(self):
        """Инициализация сервиса"""
        try:
            logger.info("Инициализация RSS парсера...")

            # Получаем URL лент из конфига
            feed_urls = Config.get_rss_feed_urls()
            logger.info(f"Настроено {len(feed_urls)} RSS лент")

            # Создаем парсер
            self.rss_parser = RSSParser(feed_urls)

            logger.info("RSS парсер инициализирован успешно")
            return True

        except Exception as e:
            logger.error(f"Ошибка инициализации RSS парсера: {e}")
            return False

    async def check_feeds(self):
        """Проверка RSS лент на новые записи"""
        try:
            logger.info("Начинаем проверку RSS лент...")
            start_time = datetime.now()

            # Получаем новые записи
            new_entries = await self.rss_parser.get_new_entries()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if new_entries:
                logger.info(
                    f"Найдено {len(new_entries)} новых/обновленных записей за {duration:.2f}с"
                )

                # Логируем информацию о найденных записях
                for entry in new_entries:
                    logger.info(
                        f"  - {entry.get('title', 'Без названия')} (work_id: {entry.get('work_id')})"
                    )
            else:
                logger.info(f"Новых записей не найдено за {duration:.2f}с")

        except Exception as e:
            logger.error(f"Ошибка при проверке RSS лент: {e}")

    async def run_periodic_check(self):
        """Запуск периодической проверки"""
        logger.info(
            f"Запуск периодической проверки каждые {Config.CHECK_INTERVAL_MINUTES} минут"
        )

        while self.running:
            try:
                await self.check_feeds()

                # Ждем до следующей проверки
                wait_seconds = Config.CHECK_INTERVAL_MINUTES * 60
                logger.info(
                    f"Ожидание {Config.CHECK_INTERVAL_MINUTES} минут до следующей проверки..."
                )

                await asyncio.sleep(wait_seconds)

            except asyncio.CancelledError:
                logger.info("Периодическая проверка отменена")
                break
            except Exception as e:
                logger.error(f"Ошибка в периодической проверке: {e}")
                # При ошибке ждем 5 минут перед следующей попыткой
                await asyncio.sleep(300)

    async def start(self):
        """Запуск сервиса"""
        if not await self.initialize():
            return False

        self.running = True
        logger.info("RSS парсер сервис запущен")

        # Запускаем периодическую проверку
        self.task = asyncio.create_task(self.run_periodic_check())

        try:
            await self.task
        except asyncio.CancelledError:
            logger.info("Сервис остановлен")
        finally:
            self.running = False

    async def stop(self):
        """Остановка сервиса"""
        logger.info("Остановка RSS парсер сервиса...")
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("RSS парсер сервис остановлен")


class BotService:
    """Сервис для отправки сообщений из очереди Redis"""

    def __init__(self):
        self.bot = None
        self.running = False
        self.task = None

    async def initialize(self):
        """Инициализация бота"""
        try:
            logger.info("Инициализация Telegram бота...")
            self.bot = RSSBot()
            logger.info("Telegram бот инициализирован успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
            return False

    async def start(self):
        """Запуск бота"""
        if not await self.initialize():
            return False

        self.running = True
        logger.info("Telegram бот запущен")

        # Запускаем периодическую обработку
        self.task = asyncio.create_task(self.bot.run_periodic_processing())
        try:
            await self.task
        except asyncio.CancelledError:
            logger.info("Бот остановлен")
        finally:
            self.running = False

    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка Telegram бота...")
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.bot:
            await self.bot.stop()

        logger.info("Telegram бот остановлен")


class FullSystemService:
    """Полная система: RSS парсер + Telegram бот"""

    def __init__(self):
        self.parser_service = RSSParserService()
        self.bot_service = BotService()
        self.running = False

    async def start(self):
        """Запуск полной системы"""
        logger.info("Запуск полной системы: RSS парсер + Telegram бот")

        # Инициализируем оба сервиса
        if not await self.parser_service.initialize():
            return False

        if not await self.bot_service.initialize():
            return False

        self.running = True

        # Запускаем оба сервиса параллельно
        parser_task = asyncio.create_task(self.parser_service.start())
        bot_task = asyncio.create_task(self.bot_service.start())

        try:
            # Ждем завершения любого из сервисов
            done, pending = await asyncio.wait(
                [parser_task, bot_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Ошибка в полной системе: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Остановка полной системы"""
        logger.info("Остановка полной системы...")
        self.running = False

        await self.parser_service.stop()
        await self.bot_service.stop()

        logger.info("Полная система остановлена")


async def main():
    """Главная функция"""
    logger.info("Запуск полной системы: RSS парсер + Telegram бот")
    logger.info(f"Интервал проверки RSS: {Config.CHECK_INTERVAL_MINUTES} минут")
    logger.info(f"Интервал отправки сообщений: {Config.SEND_INTERVAL_SECONDS} секунд")
    logger.info(f"Дней для проверки повторных отправок: {Config.DAYS_TO_CHECK}")

    # Создаем полную систему
    system = FullSystemService()

    # Настройка обработки сигналов для graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}, останавливаем систему...")
        asyncio.create_task(system.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1
    finally:
        await system.stop()

    logger.info("Полная система завершена")
    return 0


def cli_main():
    """Точка входа для CLI"""
    try:
        exit_code = asyncio.run(main())
        return exit_code
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем")
        return 0
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
