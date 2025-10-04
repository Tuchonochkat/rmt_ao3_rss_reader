#!/bin/bash
# Скрипт для первоначальной настройки проекта

set -e

echo "🚀 Настройка RSS → Telegram Bot с uv"

# Проверяем наличие uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv не найден. Устанавливаем..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "✅ uv установлен"

# Создаем виртуальное окружение и устанавливаем зависимости
echo "📦 Установка зависимостей..."
uv sync

# Копируем конфигурацию
if [ ! -f .env ]; then
    echo "📝 Создание конфигурации..."
    cp config.env.example .env
    echo "⚠️  Не забудьте отредактировать файл .env с вашими настройками!"
else
    echo "✅ Конфигурация уже существует"
fi

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте файл .env с вашими настройками"
echo "2. Запустите тест: uv run rss-bot-test"
echo "3. Запустите бота: uv run rss-bot-run"
