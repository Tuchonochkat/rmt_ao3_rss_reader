import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import feedparser

from config import Config
from utils.redis_connector import redis_connector

logger = logging.getLogger(__name__)


class RSSParser:
    """Парсер RSS лент для Archive of Our Own"""

    def __init__(self, feed_urls: list):
        self.feed_urls = feed_urls if isinstance(feed_urls, list) else [feed_urls]
        self.redis = redis_connector

    def _extract_work_id(self, entry) -> Optional[str]:
        """Извлекает work_id из записи RSS"""
        try:
            # Сначала пробуем извлечь из поля <id>
            # Пример: tag:archiveofourown.org,2005:Work/72253326
            entry_id = entry.get("id", "")
            if entry_id:
                match = re.search(r"Work/(\d+)", entry_id)
                if match:
                    return match.group(1)

            # Если не получилось, пробуем из ссылки
            link = entry.get("link", "")
            if link:
                match = re.search(r"/works/(\d+)", link)
                if match:
                    return match.group(1)

            logger.warning(
                f"Не удалось извлечь work_id из записи. ID: {entry_id}, Link: {link}"
            )
            return None
        except Exception as e:
            logger.error(f"Ошибка извлечения work_id из записи: {e}")
            return None

    def _extract_updated_date(self, entry) -> Optional[str]:
        """Извлекает дату обновления из записи RSS (только дата, без времени)"""
        try:
            # Приоритет: updated > published
            date_fields = ["updated", "published"]

            for field in date_fields:
                if hasattr(entry, field) and entry[field]:
                    date_str = entry[field]
                    if isinstance(date_str, str):
                        # Пробуем распарсить дату в формате ISO 8601
                        # Пример: 2025-10-11T08:22:00Z
                        try:
                            # Основной формат AO3: YYYY-MM-DDTHH:MM:SSZ
                            parsed_date = datetime.strptime(
                                date_str, "%Y-%m-%dT%H:%M:%SZ"
                            )
                            # Возвращаем только дату в формате YYYY-MM-DD
                            return parsed_date.strftime("%Y-%m-%d")
                        except Exception:
                            continue

            # Если не удалось распарсить, возвращаем текущую дату
            logger.warning("Не удалось извлечь дату из записи, используем текущую дату")
            return datetime.now().strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"Ошибка извлечения даты обновления: {e}")
            return datetime.now().strftime("%Y-%m-%d")

    def _extract_published_date(self, entry) -> Optional[str]:
        """Извлекает дату публикации из записи RSS (только дата, без времени)"""
        try:
            if hasattr(entry, "published") and entry.published:
                date_str = entry.published
                if isinstance(date_str, str):
                    try:
                        # Основной формат AO3: YYYY-MM-DDTHH:MM:SSZ
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                        # Возвращаем только дату в формате YYYY-MM-DD
                        return parsed_date.strftime("%Y-%m-%d")
                    except Exception:
                        pass

            # Если не удалось распарсить, возвращаем пустую строку
            logger.warning("Не удалось извлечь дату публикации из записи")
            return ""
        except Exception as e:
            logger.error(f"Ошибка извлечения даты публикации: {e}")
            return ""

    def fetch_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """Получает и парсит RSS ленту"""
        try:
            logger.info(f"Получение RSS ленты: {feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"RSS лента содержит ошибки: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning(f"RSS лента пуста: {feed_url}")
                return None

            logger.info(f"Получено {len(feed.entries)} записей из {feed_url}")
            return feed

        except Exception as e:
            logger.error(f"Ошибка при получении RSS ленты {feed_url}: {e}")
            return None

    async def get_new_entries(self) -> List[Dict]:
        """Возвращает новые записи из всех RSS лент с проверкой через Redis"""
        all_new_entries = []

        # Подключаемся к Redis
        await self.redis.connect()

        for feed_url in self.feed_urls:
            feed_url = feed_url.strip()
            if not feed_url:
                continue

            logger.info(f"Проверка ленты: {feed_url}")
            feed = self.fetch_feed(feed_url)
            if not feed:
                continue

            new_entries = []

            for entry in feed.entries:
                # Извлекаем work_id и дату обновления
                work_id = self._extract_work_id(entry)
                if not work_id:
                    logger.warning("Не удалось извлечь work_id из записи")
                    continue

                updated_date = self._extract_updated_date(entry)

                # Проверяем, есть ли данные в Redis
                existing_metadata = await self.redis.get_fanfic_metadata(work_id)

                if (
                    existing_metadata
                    and existing_metadata.get("updated_at") == updated_date
                ):
                    # Данные уже актуальны, пропускаем
                    logger.debug(f"Work {work_id} уже актуален, пропускаем")
                    continue

                # Нужно обновить или добавить данные
                logger.info(f"Обрабатываем work {work_id} (дата: {updated_date})")

                # Парсим все поля записи
                entry_data = await self._parse_entry(
                    entry, work_id, updated_date, feed_url
                )

                if entry_data:
                    # Сохраняем в Redis
                    await self.redis.save_fanfic_metadata(work_id, entry_data)

                    # Проверяем, не отправлялось ли сообщение недавно
                    was_sent_recently = await self.redis.was_message_sent_recently(
                        work_id, Config.DAYS_TO_CHECK
                    )

                    if was_sent_recently:
                        logger.info(
                            f"Work {work_id} уже отправлялся за последние {Config.DAYS_TO_CHECK} дней, пропускаем"
                        )
                    else:
                        # Добавляем в очередь только если не отправлялся недавно
                        await self.redis.add_to_queue(work_id)
                        logger.info(
                            f"Добавлен work {work_id} в очередь и сохранены метаданные"
                        )

                    new_entries.append(entry_data)

            if new_entries:
                logger.info(
                    f"Найдено {len(new_entries)} новых/обновленных записей в {feed_url}"
                )
                all_new_entries.extend(new_entries)

            # Задержка между лентами, чтобы не создавать избыточную нагрузку на сайт
            logger.debug("Ожидание 15 секунд перед обработкой следующей ленты...")
            await asyncio.sleep(15)

        if all_new_entries:
            logger.info(
                f"Всего найдено {len(all_new_entries)} новых/обновленных записей "
                f"из {len(self.feed_urls)} лент"
            )

        return all_new_entries

    async def _parse_entry(
        self, entry, work_id: str, updated_date: str, feed_url: str
    ) -> Optional[Dict]:
        """Парсит все поля записи RSS"""
        try:
            import html

            # Базовые поля
            title = html.unescape(entry.get("title", "Без названия"))
            title = re.sub(r"<[^>]+>", "", title).strip()

            link = entry.get("link", "")
            author = html.unescape(entry.get("author", "Неизвестный автор"))
            author = re.sub(r"<[^>]+>", "", author).strip()

            description = entry.get("summary", "")

            # Извлекаем метаданные из описания
            metadata = self._extract_metadata(description)

            # Формируем структурированные данные
            entry_data = {
                "work_id": work_id,
                "title": title,
                "link": link,
                "author": author,
                "published": self._extract_published_date(entry),
                "updated_at": updated_date,
                "source_feed": feed_url,
                **metadata,  # Добавляем все извлеченные метаданные
            }

            return entry_data

        except Exception as e:
            logger.error(f"Ошибка парсинга записи для work_id {work_id}: {e}")
            return None

    def _extract_metadata(self, description: str) -> Dict[str, str]:
        """Извлекает метаданные из описания работы"""
        import html
        import re

        from bs4 import BeautifulSoup

        metadata = {}

        try:
            # Парсим HTML
            soup = BeautifulSoup(description, "html.parser")

            # Ищем все li элементы с метаданными
            li_elements = soup.find_all("li")

            for li in li_elements:
                text = li.get_text().strip()

                # Фандом
                if text.startswith("Fandoms:"):
                    links = li.find_all("a")
                    if links:
                        fandoms = [link.get_text().strip() for link in links]
                        metadata["fandom"] = ", ".join(fandoms)

                # Рейтинг
                elif text.startswith("Rating:"):
                    links = li.find_all("a")
                    if links:
                        ratings = [link.get_text().strip() for link in links]
                        metadata["rating"] = ", ".join(ratings)

                # Категория
                elif text.startswith("Categories:"):
                    links = li.find_all("a")
                    if links:
                        categories = [link.get_text().strip() for link in links]
                        metadata["category"] = ", ".join(categories)

                # Предупреждения
                elif text.startswith("Warnings:"):
                    links = li.find_all("a")
                    if links:
                        warnings = [link.get_text().strip() for link in links]
                        metadata["warnings"] = ", ".join(warnings)

                # Персонажи
                elif text.startswith("Characters:"):
                    links = li.find_all("a")
                    if links:
                        characters = [link.get_text().strip() for link in links]
                        metadata["characters"] = ", ".join(characters)

                # Пейринги
                elif text.startswith("Relationships:"):
                    links = li.find_all("a")
                    if links:
                        relationships = [link.get_text().strip() for link in links]
                        metadata["relationships"] = ", ".join(relationships)

                # Дополнительные теги
                elif text.startswith("Additional Tags:"):
                    links = li.find_all("a")
                    if links:
                        tags = [link.get_text().strip() for link in links]
                        metadata["additional_tags"] = ", ".join(tags)

            # Извлекаем количество слов
            words_match = re.search(r"Words:\s*(\d+)", description)
            if words_match:
                metadata["words"] = words_match.group(1)

            # Извлекаем описание (саммари) - текст между параграфами
            paragraphs = soup.find_all("p")
            summary_parts = []
            for p in paragraphs:
                text = p.get_text().strip()
                if text and not any(
                    keyword in text.lower()
                    for keyword in [
                        "words:",
                        "chapters:",
                        "language:",
                        "fandoms:",
                        "rating:",
                        "warnings:",
                        "categories:",
                        "characters:",
                        "relationships:",
                        "additional tags:",
                    ]
                ):
                    summary_parts.append(text)

            if summary_parts:
                summary_text = " ".join(summary_parts)
                # Убираем "by <author_name>" из саммари, но только если это первый элемент
                if len(summary_parts) > 1 and summary_parts[0].lower().startswith(
                    "by "
                ):
                    # Если первый элемент начинается с "by", убираем его
                    summary_text = " ".join(summary_parts[1:])
                elif summary_text.lower().startswith("by "):
                    # Если весь текст начинается с "by", убираем только эту часть
                    summary_text = re.sub(
                        r"^by\s+[^,\s]+[,\s]*", "", summary_text, flags=re.IGNORECASE
                    ).strip()
                metadata["summary"] = summary_text

        except Exception:
            # Если BeautifulSoup не работает, используем простой regex
            import html as html_module

            clean_desc = html_module.unescape(description)

            # Простые паттерны для извлечения
            patterns = {
                "fandom": r"Fandoms:\s*<[^>]*>([^<]+)</a>",
                "rating": r"Rating:\s*<[^>]*>([^<]+)</a>",
                "category": r"Categories:\s*<[^>]*>([^<]+)</a>",
                "warnings": r"Warnings:\s*<[^>]*>([^<]+)</a>",
                "characters": r"Characters:\s*<[^>]*>([^<]+)</a>",
                "relationships": r"Relationships:\s*<[^>]*>([^<]+)</a>",
                "additional_tags": r"Additional Tags:\s*<[^>]*>([^<]+)</a>",
                "words": r"Words:\s*(\d+)",
            }

            for key, pattern in patterns.items():
                matches = re.findall(pattern, clean_desc, re.IGNORECASE)
                if matches:
                    if key == "words":
                        metadata[key] = matches[0]
                    else:
                        metadata[key] = ", ".join(matches)

        return metadata
