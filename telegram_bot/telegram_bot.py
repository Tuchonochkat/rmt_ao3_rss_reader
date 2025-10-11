import asyncio
import logging
from typing import Dict, List

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""

    def __init__(self, bot_token: str, channel_id: str):
        self.bot = Bot(token=bot_token)
        self.channel_id = channel_id

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Отправляет сообщение в канал"""
        try:
            logger.info(f"Отправляем сообщение в канал {self.channel_id}")
            logger.debug(f"Содержимое сообщения: {message[:200]}...")

            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=False,
            )
            logger.info("Сообщение успешно отправлено в канал")
            return True

        except TelegramError as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке сообщения: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def send_multiple_messages(self, messages: List[str]) -> int:
        """Отправляет несколько сообщений в канал"""
        success_count = 0

        for message in messages:
            if await self.send_message(message):
                success_count += 1
                # Небольшая задержка между сообщениями, чтобы не спамить
                await asyncio.sleep(1)

        logger.info(f"Отправлено {success_count} из {len(messages)} сообщений")
        return success_count

    async def test_connection(self) -> bool:
        """Проверяет соединение с Telegram API"""
        try:
            logger.info("Проверяем подключение к Telegram API...")
            me = await self.bot.get_me()
            logger.info(f"Бот подключен: @{me.username}")

            # Проверяем доступ к каналу
            logger.info(f"Проверяем доступ к каналу {self.channel_id}...")
            try:
                chat = await self.bot.get_chat(self.channel_id)
                logger.info(f"Доступ к каналу: {chat.title}")
                return True
            except TelegramError as e:
                logger.error(f"Нет доступа к каналу {self.channel_id}: {e}")
                return False

        except TelegramError as e:
            logger.error(f"Ошибка подключения к Telegram API: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при проверке соединения: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def format_entry_for_telegram(self, entry: Dict) -> str:
        """Форматирует запись для отправки в Telegram"""
        import html
        import re

        # Очищаем все поля от HTML
        title = html.unescape(entry["title"])
        title = re.sub(r"<[^>]+>", "", title).strip()

        # Заменяем домен .org на .gay в ссылке
        link = entry["link"].replace("archiveofourown.org", "archiveofourown.gay")

        author = html.unescape(entry["author"])
        author = re.sub(r"<[^>]+>", "", author).strip()

        # Формируем сообщение в нужном формате
        message = f"\n<a href='{link}'><b>✨✨✨{title}✨✨✨</b></a>\n"
        message += f"👤 <b>Автор:</b> {author}\n"

        # Фандом
        if entry.get("fandom"):
            message += f"🌍 <b>Фандом:</b> {entry['fandom']}\n"

        # Рейтинг
        if entry.get("rating"):
            message += f"⭐ <b>Рейтинг:</b> {entry['rating']}\n"

        # Категория
        if entry.get("category"):
            message += f"📂 <b>Категория:</b> {entry['category']}\n"

        # Предупреждения (показываем только если есть реальные предупреждения)
        if entry.get("warnings") and entry["warnings"] != "No Archive Warnings Apply":
            message += f"⚠️ <b>Предупреждения:</b> {entry['warnings']}\n"

        # Пейринги и персонажи
        relationships = entry.get("relationships", "")
        characters = entry.get("characters", "")
        if relationships or characters:
            # Выделяем пейринги жирным
            if relationships:
                relationships = f"<b>{relationships}</b>"
            message += f"💕 <b>Пейринг и персонажи:</b> {relationships}, {characters}\n"

        # Количество слов
        if entry.get("words"):
            message += f"📝 <b>Кол-во слов:</b> {entry['words']}\n"

        # Теги
        if entry.get("additional_tags"):
            message += f"🏷️ <b>Тэги:</b> {entry['additional_tags']}\n"

        # Описание
        if entry.get("summary"):
            message += f"📖 <b>Описание:</b> {entry['summary']}"

        return message
