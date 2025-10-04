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
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке сообщения: {e}")
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
            me = await self.bot.get_me()
            logger.info(f"Бот подключен: @{me.username}")

            # Проверяем доступ к каналу
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
            return False

    def format_entry_for_telegram(self, entry: Dict) -> str:
        """Форматирует запись для отправки в Telegram"""
        title = entry["title"]
        link = entry["link"]
        author = entry["author"]
        description = entry["description"]
        tags = entry["tags"]

        # Очищаем HTML теги из описания
        import re

        clean_description = re.sub(r"<[^>]+>", "", description)
        clean_description = clean_description.strip()

        # Ограничиваем длину описания
        if len(clean_description) > 300:
            clean_description = clean_description[:300] + "..."

        # Формируем сообщение
        message = f"📚 <b>{title}</b>\n\n"
        message += f"👤 Автор: {author}\n"

        if clean_description:
            message += f"📝 {clean_description}\n"

        if tags:
            tags_str = ", ".join(tags[:5])  # Показываем только первые 5 тегов
            message += f"🏷️ Теги: {tags_str}\n"

        message += f"\n🔗 <a href='{link}'>Читать на AO3</a>"

        return message
