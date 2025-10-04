import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import feedparser

logger = logging.getLogger(__name__)


class RSSParser:
    """Парсер RSS лент для Archive of Our Own"""

    def __init__(self, feed_urls: list, state_file: str = "bot_state.json"):
        self.feed_urls = feed_urls if isinstance(feed_urls, list) else [feed_urls]
        self.state_file = state_file
        self.processed_entries = self._load_state()

    def _load_state(self) -> set:
        """Загружает список уже обработанных записей"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("processed_entries", []))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Не удалось загрузить состояние: {e}")
        return set()

    def _save_state(self):
        """Сохраняет состояние обработанных записей"""
        try:
            data = {
                "processed_entries": list(self.processed_entries),
                "last_check": datetime.now().isoformat(),
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Не удалось сохранить состояние: {e}")

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

    def get_new_entries(self) -> List[Dict]:
        """Возвращает новые записи из всех RSS лент"""
        all_new_entries = []

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
                # Используем link как уникальный идентификатор
                entry_id = entry.get("link", "")
                if not entry_id:
                    continue

                if entry_id not in self.processed_entries:
                    # Формируем структурированные данные записи
                    entry_data = {
                        "id": entry_id,
                        "title": entry.get("title", "Без названия"),
                        "link": entry_id,
                        "description": entry.get("summary", ""),
                        "author": entry.get("author", "Неизвестный автор"),
                        "published": entry.get("published", ""),
                        "tags": self._extract_tags(entry),
                        "source_feed": feed_url,
                        "raw_entry": entry,
                    }

                    new_entries.append(entry_data)
                    self.processed_entries.add(entry_id)

            if new_entries:
                logger.info(f"Найдено {len(new_entries)} новых записей в {feed_url}")
                all_new_entries.extend(new_entries)

        if all_new_entries:
            logger.info(
                f"Всего найдено {len(all_new_entries)} новых записей "
                f"из {len(self.feed_urls)} лент"
            )
            self._save_state()

        return all_new_entries

    def _extract_tags(self, entry) -> List[str]:
        """Извлекает теги из записи"""
        tags = []
        import html
        import re

        # Пытаемся извлечь теги из различных полей
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                # Очищаем тег от HTML
                clean_tag = html.unescape(tag.term)
                clean_tag = re.sub(r"<[^>]+>", "", clean_tag)
                clean_tag = clean_tag.strip()
                if clean_tag:
                    tags.append(clean_tag)

        # Ищем теги в описании
        description = entry.get("summary", "")
        if "tags:" in description.lower():
            # Простое извлечение тегов из описания
            tag_matches = re.findall(r"tags?:?\s*([^\n]+)", description, re.IGNORECASE)
            for match in tag_matches:
                for tag in match.split(","):
                    clean_tag = html.unescape(tag.strip())
                    clean_tag = re.sub(r"<[^>]+>", "", clean_tag)
                    clean_tag = clean_tag.strip()
                    if clean_tag:
                        tags.append(clean_tag)

        return [
            tag for tag in tags if tag and len(tag) < 100
        ]  # Ограничиваем длину тегов

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
                # Убираем "by <author_name>" из саммари
                summary_text = re.sub(
                    r"^by\s+[^.]*\.?\s*", "", summary_text, flags=re.IGNORECASE
                ).strip()
                if summary_text.startswith("by "):
                    summary_text = summary_text[3:].strip()
                metadata["summary"] = summary_text

        except Exception as e:
            # Если BeautifulSoup не работает, используем простой regex
            import html

            clean_desc = html.unescape(description)

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

        description = entry["description"]
        tags = entry["tags"]
        source_feed = entry.get("source_feed", "")

        # Очищаем HTML теги из описания
        clean_description = html.unescape(description)
        clean_description = re.sub(r"<[^>]+>", "", clean_description)
        clean_description = re.sub(r"\s+", " ", clean_description).strip()

        # Убираем "by <author_name>" из описания
        clean_description = re.sub(
            r"^by\s+[^.]*\.?\s*", "", clean_description, flags=re.IGNORECASE
        ).strip()
        # Дополнительно убираем "by" если он остался
        if clean_description.startswith("by "):
            clean_description = clean_description[3:].strip()

        # Извлекаем метаданные из описания
        metadata = self._extract_metadata(description)

        # Формируем сообщение в нужном формате
        message = f"<a href='{link}'><b>{title}</b></a>\n"
        message += f"👤 <b>Автор:</b> {author}\n"

        # Фандом
        if metadata.get("fandom"):
            message += f"🌍 <b>Фандом:</b> {metadata['fandom']}\n"

        # Рейтинг
        if metadata.get("rating"):
            message += f"⭐ <b>Рейтинг:</b> {metadata['rating']}\n"

        # Категория
        if metadata.get("category"):
            message += f"📂 <b>Категория:</b> {metadata['category']}\n"

        # Предупреждения (показываем только если есть реальные предупреждения)
        if (
            metadata.get("warnings")
            and metadata["warnings"] != "No Archive Warnings Apply"
        ):
            message += f"⚠️ <b>Предупреждения:</b> {metadata['warnings']}\n"

        # Пейринги и персонажи
        relationships = metadata.get("relationships", "")
        characters = metadata.get("characters", "")
        if relationships or characters:
            # Выделяем пейринги жирным
            if relationships:
                relationships = f"<b>{relationships}</b>"
            message += f"💕 <b>Пейринг и персонажи:</b> {relationships}, {characters}\n"

        # Количество слов
        if metadata.get("words"):
            message += f"📝 <b>Кол-во слов:</b> {metadata['words']}\n"

        # Теги
        if metadata.get("additional_tags"):
            message += f"🏷️ <b>Тэги:</b> {metadata['additional_tags']}\n"

        # Описание
        if metadata.get("summary"):
            message += f"📖 <b>Описание:</b> {metadata['summary']}"
        elif clean_description:
            message += f"📖 <b>Описание:</b> {clean_description}"

        return message

    def _extract_feed_name(self, feed_url: str) -> str:
        """Извлекает понятное название ленты из URL"""
        try:
            # Сначала пытаемся получить описание из конфигурации
            from config import Config

            description = Config.get_feed_description(feed_url)
            if description != "Unknown Feed":
                return description

            # Если не найдено в конфигурации, извлекаем из URL
            if "tags/" in feed_url:
                # Извлекаем ID тега
                parts = feed_url.split("tags/")[1].split("/")[0]
                return f"Tag ID: {parts}"
            elif "users/" in feed_url:
                # Извлекаем имя пользователя
                parts = feed_url.split("users/")[1].split("/")[0]
                return f"Автор: {parts}"
            else:
                return "AO3"
        except Exception:
            return "AO3"
