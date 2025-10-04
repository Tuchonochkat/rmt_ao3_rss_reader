import asyncio
import logging
import time
from datetime import datetime

import schedule

from config import Config
from rss_parser import RSSParser
from telegram_bot import TelegramNotifier

# from typing import Dict, List  # Не используется


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class RSSBot:
    """Основной класс бота для интеграции RSS → Telegram"""

    def __init__(self):
        # Валидация конфигурации
        Config.validate()

        # Инициализация компонентов
        self.rss_parser = RSSParser(Config.get_rss_feed_urls(), Config.STATE_FILE)
        self.telegram_notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHANNEL_ID
        )

        logger.info("RSS Bot инициализирован")

    async def check_and_send_new_entries(self):
        """Проверяет RSS ленты и отправляет новые записи в Telegram"""
        try:
            logger.info(
                f"Проверка новых записей в {len(Config.get_rss_feed_urls())} RSS лентах..."
            )

            # Получаем новые записи
            new_entries = self.rss_parser.get_new_entries()

            if not new_entries:
                logger.info("Новых записей не найдено")
                return

            logger.info(f"Найдено {len(new_entries)} новых записей")

            # Группируем записи по источникам для статистики
            sources = {}
            for entry in new_entries:
                source = entry.get("source_feed", "Неизвестный источник")
                sources[source] = sources.get(source, 0) + 1

            logger.info(f"Статистика по источникам: {sources}")

            # Форматируем сообщения для Telegram
            messages = []
            for entry in new_entries:
                message = self.telegram_notifier.format_entry_for_telegram(entry)
                messages.append(message)

            # Отправляем сообщения
            success_count = await self.telegram_notifier.send_multiple_messages(
                messages
            )
            logger.info(
                f"Успешно отправлено {success_count} из {len(messages)} сообщений"
            )

        except Exception as e:
            logger.error(f"Ошибка при проверке и отправке записей: {e}")

    async def test_connection(self) -> bool:
        """Тестирует соединение с Telegram"""
        return await self.telegram_notifier.test_connection()

    async def send_test_message(self) -> bool:
        """Отправляет тестовое сообщение"""
        feed_info = Config.get_feed_info()
        feeds_info = "\n".join(
            [f"• {description}" for description in feed_info.values()]
        )

        test_message = (
            f"🤖 <b>RSS Bot запущен!</b>\n\n"
            f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"📡 RSS ленты ({len(Config.get_rss_feed_urls())}):\n{feeds_info}\n"
            f"🔄 Интервал проверки: {Config.CHECK_INTERVAL_MINUTES} минут"
        )

        return await self.telegram_notifier.send_message(test_message)

    def run_scheduler(self):
        """Запускает планировщик задач"""
        logger.info(
            f"Запуск планировщика с интервалом {Config.CHECK_INTERVAL_MINUTES} минут"
        )

        # Настраиваем расписание
        schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(
            lambda: asyncio.run(self.check_and_send_new_entries())
        )

        # Основной цикл
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(60)  # Ждем минуту перед повтором

    async def run_once(self):
        """Запускает одну проверку (для тестирования)"""
        logger.info("Запуск одноразовой проверки...")
        await self.check_and_send_new_entries()


async def main():
    """Основная функция"""
    bot = RSSBot()

    # Тестируем соединение
    logger.info("Тестирование соединения с Telegram...")
    if not await bot.test_connection():
        logger.error("Не удалось подключиться к Telegram. Проверьте настройки.")
        return

    # Отправляем тестовое сообщение
    logger.info("Отправка тестового сообщения...")
    if await bot.send_test_message():
        logger.info("Тестовое сообщение отправлено успешно")
    else:
        logger.error("Не удалось отправить тестовое сообщение")
        return

    # Запускаем планировщик
    logger.info("Запуск основного цикла...")
    bot.run_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
