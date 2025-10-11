import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import redis.asyncio as aioredis
from redis.asyncio import Redis

from config import Config

logger = logging.getLogger(__name__)


class RedisConnector:
    """Класс для работы с Redis для RSS бота"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            # Проверяем соединение
            await self.redis.ping()
            logger.info("Подключение к Redis установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            raise

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Отключение от Redis")

    async def _ensure_connected(self):
        """Проверяет, что соединение с Redis установлено"""
        if not self.redis:
            await self.connect()

    # Методы для работы с fanfic:metadata:{work_id}
    async def save_fanfic_metadata(self, work_id: str, metadata: Dict) -> bool:
        """
        Сохраняет метаданные фанфика

        Args:
            work_id: ID работы
            metadata: Словарь с метаданными (title, author, summary, updated_at, chapters, words и т.д.)
        """
        try:
            await self._ensure_connected()
            key = f"fanfic:metadata:{work_id}"

            # Добавляем timestamp если его нет
            if "updated_at" not in metadata:
                metadata["updated_at"] = datetime.now().strftime("%Y-%m-%d")

            # Сохраняем как Hash
            await self.redis.hset(key, mapping=metadata)
            logger.debug(f"Сохранены метаданные для work_id: {work_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных для {work_id}: {e}")
            return False

    async def get_fanfic_metadata(self, work_id: str) -> Optional[Dict]:
        """
        Получает метаданные фанфика

        Args:
            work_id: ID работы

        Returns:
            Словарь с метаданными или None если не найдено
        """
        try:
            await self._ensure_connected()
            key = f"fanfic:metadata:{work_id}"

            metadata = await self.redis.hgetall(key)
            if metadata:
                # Конвертируем bytes в строки
                return {k.decode(): v.decode() for k, v in metadata.items()}
            return None
        except Exception as e:
            logger.error(f"Ошибка получения метаданных для {work_id}: {e}")
            return None

    async def delete_fanfic_metadata(self, work_id: str) -> bool:
        """Удаляет метаданные фанфика"""
        try:
            await self._ensure_connected()
            key = f"fanfic:metadata:{work_id}"
            result = await self.redis.delete(key)
            logger.debug(f"Удалены метаданные для work_id: {work_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Ошибка удаления метаданных для {work_id}: {e}")
            return False

    # Методы для работы с channel:sent_messages
    async def save_sent_message(
        self, work_id: str, message_id: str, updated_at: Optional[str] = None
    ) -> bool:
        """
        Сохраняет информацию об отправленном сообщении

        Args:
            work_id: ID работы
            message_id: ID сообщения в Telegram
            updated_at: Время обновления (если не указано, используется текущее время)
        """
        try:
            await self._ensure_connected()
            key = "channel:sent_messages"

            if updated_at is None:
                updated_at = datetime.now().strftime("%Y-%m-%d")

            # Сохраняем как message_id:updated_at
            value = f"{message_id}:{updated_at}"
            await self.redis.hset(key, work_id, value)
            logger.debug(
                f"Сохранена информация об отправленном сообщении для work_id: {work_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка сохранения информации об отправленном сообщении для {work_id}: {e}"
            )
            return False

    async def get_sent_message(self, work_id: str) -> Optional[Tuple[str, str]]:
        """
        Получает информацию об отправленном сообщении

        Args:
            work_id: ID работы

        Returns:
            Кортеж (message_id, updated_at) или None если не найдено
        """
        try:
            await self._ensure_connected()
            key = "channel:sent_messages"

            value = await self.redis.hget(key, work_id)
            if value:
                message_id, updated_at = value.decode().split(":", 1)
                return message_id, updated_at
            return None
        except Exception as e:
            logger.error(
                f"Ошибка получения информации об отправленном сообщении для {work_id}: {e}"
            )
            return None

    async def get_all_sent_messages(self) -> Dict[str, Tuple[str, str]]:
        """
        Получает все отправленные сообщения

        Returns:
            Словарь {work_id: (message_id, updated_at)}
        """
        try:
            await self._ensure_connected()
            key = "channel:sent_messages"

            messages = await self.redis.hgetall(key)
            result = {}
            for work_id_bytes, value_bytes in messages.items():
                work_id = work_id_bytes.decode()
                message_id, updated_at = value_bytes.decode().split(":", 1)
                result[work_id] = (message_id, updated_at)
            return result
        except Exception as e:
            logger.error(f"Ошибка получения всех отправленных сообщений: {e}")
            return {}

    async def delete_sent_message(self, work_id: str) -> bool:
        """Удаляет информацию об отправленном сообщении"""
        try:
            await self._ensure_connected()
            key = "channel:sent_messages"
            result = await self.redis.hdel(key, work_id)
            logger.debug(
                f"Удалена информация об отправленном сообщении для work_id: {work_id}"
            )
            return bool(result)
        except Exception as e:
            logger.error(
                f"Ошибка удаления информации об отправленном сообщении для {work_id}: {e}"
            )
            return False

    async def was_message_sent_recently(self, work_id: str, days: int) -> bool:
        """
        Проверяет, отправлялось ли сообщение за последние N дней

        Args:
            work_id: ID работы
            days: Количество дней для проверки

        Returns:
            True если сообщение отправлялось за последние N дней, False иначе
        """
        try:
            await self._ensure_connected()
            key = "channel:sent_messages"

            # Получаем информацию о сообщении
            value = await self.redis.hget(key, work_id)
            if not value:
                return False

            # Парсим значение: message_id:updated_at
            try:
                message_id, sent_at_str = value.decode().split(":", 1)
            except ValueError:
                logger.warning(
                    f"Некорректный формат данных для work_id {work_id}: {value}"
                )
                return False

            # Парсим дату отправки
            from datetime import datetime, timedelta

            try:
                # Формат: YYYY-MM-DDTHH:MM:SSZ
                sent_at = datetime.strptime(sent_at_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                try:
                    # Альтернативный формат: YYYY-MM-DD
                    sent_at = datetime.strptime(sent_at_str, "%Y-%m-%d")
                except ValueError:
                    logger.warning(
                        f"Некорректный формат даты для work_id {work_id}: {sent_at_str}"
                    )
                    return False

            # Проверяем, прошло ли достаточно времени
            cutoff_date = datetime.now() - timedelta(days=days)
            was_sent_recently = sent_at > cutoff_date

            if was_sent_recently:
                logger.debug(
                    f"Сообщение для work_id {work_id} отправлялось {sent_at_str} (в пределах {days} дней)"
                )
            else:
                logger.debug(
                    f"Сообщение для work_id {work_id} отправлялось {sent_at_str} (более {days} дней назад)"
                )

            return was_sent_recently

        except Exception as e:
            logger.error(
                f"Ошибка проверки недавних отправок для work_id {work_id}: {e}"
            )
            return False

    # Методы для работы с queue:new_fanfics
    async def add_to_queue(self, work_id: str) -> bool:
        """
        Добавляет work_id в очередь новых фанфиков

        Args:
            work_id: ID работы для добавления в очередь
        """
        try:
            await self._ensure_connected()
            key = "queue:new_fanfics"
            await self.redis.lpush(key, work_id)
            logger.debug(f"Добавлен в очередь: {work_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в очередь {work_id}: {e}")
            return False

    async def get_from_queue(self, timeout: int = 0) -> Optional[str]:
        """
        Получает work_id из очереди

        Args:
            timeout: Время ожидания в секундах (0 = не ждать)

        Returns:
            work_id или None если очередь пуста
        """
        try:
            await self._ensure_connected()
            key = "queue:new_fanfics"

            if timeout > 0:
                # Блокирующее получение
                result = await self.redis.brpop(key, timeout=timeout)
                if result:
                    return result[1].decode()
            else:
                # Неблокирующее получение
                result = await self.redis.rpop(key)
                if result:
                    return result.decode()
            return None
        except Exception as e:
            logger.error(f"Ошибка получения из очереди: {e}")
            return None

    async def get_queue_length(self) -> int:
        """Возвращает длину очереди"""
        try:
            await self._ensure_connected()
            key = "queue:new_fanfics"
            return await self.redis.llen(key)
        except Exception as e:
            logger.error(f"Ошибка получения длины очереди: {e}")
            return 0

    async def clear_queue(self) -> bool:
        """Очищает очередь"""
        try:
            await self._ensure_connected()
            key = "queue:new_fanfics"
            await self.redis.delete(key)
            logger.debug("Очередь очищена")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки очереди: {e}")
            return False

    # Вспомогательные методы
    async def get_all_fanfic_ids(self) -> List[str]:
        """Получает все work_id из метаданных"""
        try:
            await self._ensure_connected()
            pattern = "fanfic:metadata:*"
            keys = await self.redis.keys(pattern)
            return [key.decode().replace("fanfic:metadata:", "") for key in keys]
        except Exception as e:
            logger.error(f"Ошибка получения всех work_id: {e}")
            return []

    async def cleanup_old_data(self, days_old: int = 30) -> int:
        """
        Очищает старые данные

        Args:
            days_old: Количество дней для определения "старых" данных

        Returns:
            Количество удаленных записей
        """
        try:
            await self._ensure_connected()
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0

            # Получаем все метаданные
            fanfic_ids = await self.get_all_fanfic_ids()

            for work_id in fanfic_ids:
                metadata = await self.get_fanfic_metadata(work_id)
                if metadata and "updated_at" in metadata:
                    try:
                        # Парсим дату в формате YYYY-MM-DD
                        updated_at = datetime.strptime(
                            metadata["updated_at"], "%Y-%m-%d"
                        )
                        if updated_at.timestamp() < cutoff_date:
                            await self.delete_fanfic_metadata(work_id)
                            await self.delete_sent_message(work_id)
                            deleted_count += 1
                    except ValueError:
                        # Если не можем распарсить дату, пропускаем
                        continue

            logger.info(f"Очищено {deleted_count} старых записей")
            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}")
            return 0

    async def get_stats(self) -> Dict:
        """Возвращает статистику по Redis"""
        try:
            await self._ensure_connected()

            fanfic_count = len(await self.get_all_fanfic_ids())
            sent_messages = await self.get_all_sent_messages()
            queue_length = await self.get_queue_length()

            return {
                "fanfic_metadata_count": fanfic_count,
                "sent_messages_count": len(sent_messages),
                "queue_length": queue_length,
                "redis_info": await self.redis.info(),
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}


# Глобальный экземпляр для использования в приложении
redis_connector = RedisConnector(Config.REDIS_URL)
