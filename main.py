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

        # Запускаем бота
        self.task = asyncio.create_task(self.bot.start())
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
        logger.info("Инициализация RSS парсер сервиса...")
        if not await self.parser_service.initialize():
            logger.error("Ошибка инициализации RSS парсер сервиса")
            return False
        logger.info("RSS парсер сервис инициализирован успешно")

        logger.info("Инициализация Telegram бот сервиса...")
        if not await self.bot_service.initialize():
            logger.error("Ошибка инициализации Telegram бот сервиса")
            return False
        logger.info("Telegram бот сервис инициализирован успешно")

        self.running = True

        # Запускаем оба сервиса параллельно
        logger.info("Запуск RSS парсер сервиса...")
        parser_task = asyncio.create_task(self.parser_service.start())

        logger.info("Запуск Telegram бот сервиса...")
        bot_task = asyncio.create_task(self.bot_service.start())

        try:
            # Ждем завершения обоих сервисов
            logger.info("Ожидание завершения сервисов...")

            # Создаем задачи для мониторинга
            tasks = [parser_task, bot_task]

            while self.running:
                try:
                    # Ждем завершения любого из сервисов
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )

                    # Проверяем результаты
                    for task in done:
                        try:
                            result = await task
                            if result is False:
                                logger.error("Один из сервисов завершился с ошибкой")
                                self.running = False
                                break
                        except Exception as e:
                            logger.error(f"Сервис завершился с ошибкой: {e}")
                            self.running = False
                            break

                    # Если все задачи завершены, выходим
                    if not pending:
                        logger.info("Все сервисы завершили работу")
                        break

                except asyncio.CancelledError:
                    logger.info("Получен сигнал отмены")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в мониторинге сервисов: {e}")
                    break

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

    # Проверяем конфигурацию
    try:
        Config.validate()
        logger.info("Конфигурация валидна")
    except Exception as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return 1

    logger.info(f"Интервал проверки RSS: {Config.CHECK_INTERVAL_MINUTES} минут")
    logger.info(f"Интервал отправки сообщений: {Config.SEND_INTERVAL_SECONDS} секунд")
    logger.info(f"Дней для проверки повторных отправок: {Config.DAYS_TO_CHECK}")

    # Проверяем количество RSS лент
    feed_urls = Config.get_rss_feed_urls()
    logger.info(f"Настроено RSS лент: {len(feed_urls)}")
    if not feed_urls:
        logger.error("Не настроено ни одной RSS ленты!")
        return 1

    # Создаем полную систему
    system = FullSystemService()

    # Настройка обработки сигналов для graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}, останавливаем систему...")
        asyncio.create_task(system.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("Начинаем запуск системы...")
        await system.start()
        logger.info("Система успешно запущена")
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        logger.info("Останавливаем систему...")
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
