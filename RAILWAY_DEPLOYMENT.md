# Развертывание на Railway

## Настройка проекта

### 1. Переменные окружения

Установите следующие переменные окружения в Railway:

#### Обязательные переменные:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
REDIS_URL=your_redis_url_here
```

#### Опциональные переменные:
```
CHECK_INTERVAL_MINUTES=30
DAYS_TO_CHECK=3
SEND_INTERVAL_SECONDS=300
LOG_LEVEL=INFO
```

### 2. Railway Volumes (если нужны логи)

Если вы хотите сохранять логи в файлы, настройте Railway volume:

1. В панели управления Railway перейдите в настройки сервиса
2. Добавьте Volume с путем `/app/logs`
3. Обновите код логирования для использования этого пути

### 3. Настройка Redis

Railway предоставляет Redis как отдельный сервис:

1. Добавьте Redis сервис в ваш проект
2. Скопируйте `REDIS_URL` из настроек Redis сервиса
3. Установите эту переменную в вашем основном сервисе

## Структура проекта

Railway автоматически обнаружит `Dockerfile` в корне проекта и использует его для сборки.

## Мониторинг

- Логи доступны в панели Railway в реальном времени
- Railway автоматически перезапускает сервис при сбоях
- Используйте Railway CLI для управления деплоем

## Команды для локальной разработки

```bash
# Установка Railway CLI
npm install -g @railway/cli

# Логин в Railway
railway login

# Подключение к проекту
railway link

# Деплой
railway up

# Просмотр логов
railway logs
```

## Troubleshooting

### Ошибка "VOLUME keyword is banned"
- ✅ Исправлено: удалена строка `VOLUME ["/app/logs"]` из Dockerfile

### Ошибка "Readme file does not exist: README.md"
- ✅ Исправлено: README.md теперь копируется до установки зависимостей
- ✅ Исправлено: убрано исключение README.md из .dockerignore
- Если проблема повторяется, можно временно убрать `readme = "README.md"` из pyproject.toml

### Ошибка "Permission denied" для uv cache
- ✅ Исправлено: добавлен флаг `-m` при создании пользователя для создания домашней директории
- ✅ Исправлено: установлена переменная `UV_CACHE_DIR=/app/.uv_cache`
- ✅ Исправлено: создана директория кэша с правильными правами

### Проблемы с Redis подключением
- Убедитесь, что `REDIS_URL` правильно настроен
- Проверьте, что Redis сервис запущен в Railway

### Проблемы с Telegram
- Проверьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHANNEL_ID`
- Убедитесь, что бот добавлен в канал как администратор
