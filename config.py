import os

from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Конфигурация приложения"""

    REDIS_URL = os.getenv("REDIS_URL")

    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

    # RSS настройки
    # Базовый URL для формирования ссылок
    RSS_BASE_URL = "https://archiveofourown.gay/tags/{tag_id}/feed.atom"

    # Словарь RSS лент: {ID: "Описание тега"}
    RSS_FEEDS = {
        "31415212": "Russian Actor RPF",
        "64246090": "Икар - Круглов/Макуни | Icarus - Kruglov/Makuni",
        "60197176": "Последнее испытание - Круглов и Ханпира | The Last Trial - Kruglov & Khanpira",
        "86160696": "Лэ о Лэйтиан - Смеркович и Сидоренко | The Lay of Leithian - Smerkovich & Sidorenko",
        "121446937": "Книга Стихий - Антипов&Мажуга/Батурина&Ересина | Book of Elements - Antipov&Mazhuga/Baturina&Eresina",
        "120823408": " Эльфийская Рукопись - Эпидемия | Elven Manuscript - Epidemia (Albums)",
        "143279551": "Детективная сага — Ярослав Баярунас",
        "130948627": "Жанна д‘Арк - Бочарова/Воробьёва/Каковиди/Сусоров | Joan of Arc - Bocharova/Vorobyova/Kakovidi/Susorov",
        "68767828": "Монте Кристо - Игнатьев/Ким | Monte Cristo - Ignatiev/Kim",
        "94785088": "Орфей - Вайнер | Orpheus - Weiner",  # всего 12 работ
        # "504856": "Jesus Christ Superstar - Webber/Rice",  # тут надо фильтроваться по языку
        "23355485": "The Grinning Man - Philips & Teitler/Grose & Morris & Philips & Teitler/Grose",
        "107185864": "Вий - Байдо и Загот/Захарова/Петрановская | Viy - Baido & Zagot/Zakharova/Petranovskaya",  # всего 6 работ
        "116213980": "Айсвилль - Загот/Рубинский | Iceville - Zagot/Rubinsky",
    }

    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))

    # Количество дней для проверки повторных отправок
    DAYS_TO_CHECK = int(os.getenv("DAYS_TO_CHECK", "3"))

    # Интервал отправки сообщений (минуты)
    SEND_INTERVAL_SECONDS = int(os.getenv("SEND_INTERVAL_SECONDS", "5"))

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
        if not cls.REDIS_URL:
            raise ValueError("REDIS_URL не установлен")
