import os

from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Конфигурация приложения"""

    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

    # RSS настройки
    # Базовый URL для формирования ссылок
    RSS_BASE_URL = "https://archiveofourown.gay/tags/{tag_id}/feed.atom"

    # Словарь RSS лент: {ID: "Описание тега"}
    RSS_FEEDS = {
        "31415212": "Russian Actor RPF",  # Русские актеры РМТ
        # "136512": "Harry Potter - J. K. Rowling",  # Милые работы
    }

    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))

    # Логирование
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Файл для хранения последних обработанных записей
    STATE_FILE = "bot_state.json"

    @classmethod
    def get_rss_feed_urls(cls) -> list:
        """Возвращает список URL RSS лент"""
        return [
            cls.RSS_BASE_URL.format(tag_id=tag_id) for tag_id in cls.RSS_FEEDS.keys()
        ]

    @classmethod
    def get_feed_description(cls, feed_url: str) -> str:
        """Получает описание тега по URL RSS ленты"""
        for tag_id, description in cls.RSS_FEEDS.items():
            if tag_id in feed_url:
                return description
        return "Unknown Feed"

    @classmethod
    def get_feed_info(cls) -> dict:
        """Возвращает информацию о всех RSS лентах"""
        urls = cls.get_rss_feed_urls()
        return {
            url: cls.RSS_FEEDS.get(tag_id, "Unknown")
            for tag_id, url in zip(cls.RSS_FEEDS.keys(), urls)
        }

    @classmethod
    def validate(cls):
        """Проверяет корректность конфигурации"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not cls.TELEGRAM_CHANNEL_ID:
            raise ValueError("TELEGRAM_CHANNEL_ID не установлен")
        if not cls.RSS_FEEDS:
            raise ValueError("RSS_FEEDS не настроены")
