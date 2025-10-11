import asyncio
import logging
import sys
from datetime import datetime

from config import Config
from telegram_bot.telegram_bot import TelegramNotifier
from utils.redis_connector import redis_connector

logger = logging.getLogger(__name__)


class RSSBot:
    """Основной класс бота для работы с очередью Redis"""

    def __init__(self):
        self.telegram_notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHANNEL_ID
        )
        self.redis = redis_connector
        self.running = False

    async def process_queue_item(self, work_id: str) -> bool:
        """Обрабатывает один элемент из очереди"""
        try:
            logger.info(f"Обрабатываем work_id: {work_id}")

            # Получаем метаданные из Redis
            metadata = await self.redis.get_fanfic_metadata(work_id)
            if not metadata:
                logger.warning(f"Метаданные для work_id {work_id} не найдены")
                return False

            # Форматируем сообщение
            message = self.telegram_notifier.format_entry_for_telegram(metadata)

            # Отправляем сообщение
            success = await self.telegram_notifier.send_message(message)
            if not success:
                logger.error(f"Не удалось отправить сообщение для work_id {work_id}")
                return False

            # Записываем в channel:sent_messages
            current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            await self.redis.save_sent_message(work_id, "sent", current_time)

            logger.info(f"Сообщение для work_id {work_id} успешно отправлено")
            return True

        except Exception as e:
            logger.error(f"Ошибка обработки work_id {work_id}: {e}")
            return False

    async def process_queue(self) -> int:
        """Обрабатывает очередь Redis"""
        try:
            # Получаем длину очереди
            queue_length = await self.redis.get_queue_length()
            if queue_length == 0:
                logger.debug("Очередь пуста")
                return 0

            logger.info(f"В очереди {queue_length} элементов")

            # Обрабатываем один элемент
            work_id = await self.redis.get_from_queue(timeout=0)
            if not work_id:
                logger.debug("Не удалось получить элемент из очереди")
                return 0

            # Обрабатываем элемент
            success = await self.process_queue_item(work_id)
            return 1 if success else 0

        except Exception as e:
            logger.error(f"Ошибка обработки очереди: {e}")
            return 0

    async def run_periodic_processing(self):
        """Запускает периодическую обработку очереди"""
        logger.info(
            f"Запуск периодической обработки каждые {Config.SEND_INTERVAL_SECONDS} секунд"
        )

        while self.running:
            try:
                # Обрабатываем очередь
                processed = await self.process_queue()

                if processed > 0:
                    logger.info(f"Обработано {processed} элементов из очереди")
                else:
                    logger.debug("Очередь пуста, ожидание...")

                # Ждем до следующей обработки
                wait_seconds = Config.SEND_INTERVAL_SECONDS
                logger.debug(
                    f"Ожидание {Config.SEND_INTERVAL_SECONDS} секунд до следующей обработки..."
                )

                await asyncio.sleep(wait_seconds)

            except asyncio.CancelledError:
                logger.info("Периодическая обработка отменена")
                break
            except Exception as e:
                logger.error(f"Ошибка в периодической обработке: {e}")
                # При ошибке ждем 5 минут перед следующей попыткой
                await asyncio.sleep(300)

    async def start(self):
        """Запускает бота"""
        logger.info("Запуск RSS бота...")

        # Подключаемся к Redis
        await self.redis.connect()

        # Проверяем соединение с Telegram
        if not await self.telegram_notifier.test_connection():
            logger.error("Не удалось подключиться к Telegram")
            return False

        self.running = True
        logger.info("RSS бот запущен")

        # Запускаем периодическую обработку
        await self.run_periodic_processing()

        return True

    async def stop(self):
        """Останавливает бота"""
        logger.info("Остановка RSS бота...")
        self.running = False
        logger.info("RSS бот остановлен")


async def main():
    """Главная функция"""
    logger.info("Запуск RSS бота")
    logger.info(f"Интервал отправки: {Config.SEND_INTERVAL_SECONDS} секунд")

    # Создаем бота
    bot = RSSBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1
    finally:
        await bot.stop()

    logger.info("RSS бот завершен")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        sys.exit(1)
