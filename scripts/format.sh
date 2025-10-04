#!/bin/bash
# Скрипт для форматирования кода

set -e

echo "🎨 Форматирование кода..."

# Устанавливаем инструменты разработки
uv sync --extra dev

# Форматируем код
echo "📝 Форматирование с black..."
uv run black .

echo "📦 Сортировка импортов с isort..."
uv run isort .

echo "🔍 Проверка с flake8..."
uv run flake8 . --exclude=.venv

echo "✅ Код отформатирован!"
