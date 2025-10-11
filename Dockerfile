# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv

# Создаем пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей и README
COPY pyproject.toml uv.lock README.md ./

# Устанавливаем зависимости
RUN /uv/bin/uv sync --frozen

# Копируем остальной исходный код
COPY . .

# Создаем директории и устанавливаем права
RUN mkdir -p /app/logs /app/.uv_cache && chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV UV_CACHE_DIR=/app/.uv_cache

# Команда по умолчанию
CMD ["/uv/bin/uv", "run", "python", "main.py"]
