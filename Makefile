.PHONY: help install test run format clean setup dev

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Первоначальная настройка проекта
	@echo "🚀 Настройка проекта..."
	@./scripts/setup.sh

install: ## Установка зависимостей
	@echo "📦 Установка зависимостей..."
	@uv sync

dev: ## Установка зависимостей для разработки
	@echo "🔧 Установка зависимостей для разработки..."
	@uv sync --extra dev

test: ## Запуск тестов
	@echo "🧪 Запуск тестов..."
	@uv run rss-bot-test

run: ## Запуск бота
	@echo "🚀 Запуск бота..."
	@uv run rss-bot-run

format: ## Форматирование кода
	@echo "🎨 Форматирование кода..."
	@./scripts/format.sh

clean: ## Очистка временных файлов
	@echo "🧹 Очистка..."
	@rm -rf .venv/
	@rm -f bot.log
	@rm -f bot_state.json

dev-run: ## Запуск в режиме разработки
	@echo "🔧 Запуск в режиме разработки..."
	@./scripts/dev.sh

check: ## Проверка кода
	@echo "🔍 Проверка кода..."
	@uv run flake8 .
	@uv run mypy .

update: ## Обновление зависимостей
	@echo "🔄 Обновление зависимостей..."
	@uv lock --upgrade
	@uv sync
