# RMT AO3 RSS Bot

Этот бот автоматически отслеживает RSS ленты Archive of Our Own (AO3) и отправляет новые записи в ваш Telegram-канал.

## Возможности

- 📡 **Множественные RSS ленты** - отслеживание нескольких лент одновременно
- 🤖 Отправка уведомлений в Telegram-канал
- 🔄 Настраиваемый интервал проверки
- 📝 Красивое форматирование сообщений с указанием источника
- 🏷️ Отображение тегов и авторов
- 💾 Сохранение состояния (избегает дублирования)
- 📊 Подробное логирование и статистика по источникам
- ⚡ Быстрая установка с помощью `uv`
- 🔄 Обратная совместимость со старыми конфигурациями

## Установка

### 1. Установка uv (если не установлен)

```bash
# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Или через pip
pip install uv
```

### 2. Клонирование и установка зависимостей

```bash
# Создание виртуального окружения и установка зависимостей
uv sync

# Или для разработки с дополнительными инструментами
uv sync --extra dev
```

### 3. Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 4. Настройка канала

1. Создайте публичный канал в Telegram
2. Добавьте вашего бота как администратора канала
3. Узнайте ID канала (начинается с @) или числовой ID

### 5. Настройка конфигурации

Скопируйте файл конфигурации и заполните его:

```bash
cp config.env.example .env
```

Отредактируйте файл `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_username

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# RSS Configuration
# Поддержка множественных RSS лент (через запятую)
RSS_FEED_URLS=https://archiveofourown.org/works/feed,https://archiveofourown.org/tags/Real%20Person%20Fiction/feed,https://archiveofourown.org/tags/Fluff/feed
# Для обратной совместимости (если указан, будет добавлен к RSS_FEED_URLS)
# RSS_FEED_URL=https://archiveofourown.org/works/feed
CHECK_INTERVAL_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

## Использование

### Быстрый старт

```bash
# Автоматическая настройка
make setup

# Или вручную
./scripts/setup.sh
```

### Тестирование

Перед запуском в продакшене рекомендуется протестировать бота:

```bash
# С помощью uv
uv run python telegram_bot/test_bot.py

# Или используя скрипт из pyproject.toml
uv run rss-bot-test

# Или через Makefile
make test
```

Этот скрипт:
- Проверит соединение с Telegram
- Отправит тестовое сообщение
- Выполнит одну проверку RSS ленты

### Запуск RSS парсера

Для периодической проверки RSS лент:

```bash
# С помощью uv
uv run python main.py

# Или используя скрипт из pyproject.toml
uv run rss-parser

# Или через Makefile
make parser
```

### Запуск бота

Для постоянной работы:

```bash
# С помощью uv
uv run python telegram_bot/run_bot.py

# Или используя скрипт из pyproject.toml
uv run rss-bot-run

# Или через Makefile
make run
```

Или напрямую:

```bash
uv run python telegram_bot/bot.py
```

### Команды Makefile

```bash
make help          # Показать все доступные команды
make setup         # Первоначальная настройка
make install       # Установка зависимостей
make dev           # Установка зависимостей для разработки
make test          # Запуск тестов
make run           # Запуск бота
make format        # Форматирование кода
make clean         # Очистка временных файлов
make dev-run       # Запуск в режиме разработки
make check         # Проверка кода
make update        # Обновление зависимостей
```

## Настройка RSS лент

### Поддержка множественных лент

Бот теперь поддерживает **несколько RSS лент одновременно**! Это позволяет отслеживать разные теги, фандомы или авторов в одном канале.

### Основные RSS ленты AO3

- **Все работы**: `https://archiveofourown.org/works/feed`
- **По фандому**: `https://archiveofourown.org/tags/[fandom_name]/feed`
- **По тегу**: `https://archiveofourown.org/tags/[tag_name]/feed`
- **По автору**: `https://archiveofourown.org/users/[username]/feed`

### Примеры конфигурации

#### Одна лента (обратная совместимость):
```env
RSS_FEED_URL=https://archiveofourown.org/works/feed
```

#### Несколько лент (рекомендуется):
```env
# РМТ + Fluff + все работы
RSS_FEED_URLS=https://archiveofourown.org/works/feed,https://archiveofourown.org/tags/Real%20Person%20Fiction/feed,https://archiveofourown.org/tags/Fluff/feed

# Конкретные фандомы
RSS_FEED_URLS=https://archiveofourown.org/tags/Harry%20Potter%20-J.K.%20Rowling/feed,https://archiveofourown.org/tags/Marvel%20Cinematic%20Universe/feed

# Следить за конкретными авторами
RSS_FEED_URLS=https://archiveofourown.org/users/author1/feed,https://archiveofourown.org/users/author2/feed
```

### Популярные теги для РМТ

```env
# РМТ теги
RSS_FEED_URLS=https://archiveofourown.org/tags/Real%20Person%20Fiction/feed,https://archiveofourown.org/tags/Fluff/feed,https://archiveofourown.org/tags/Angst/feed,https://archiveofourown.org/tags/Romance/feed
```

### Готовая конфигурация для РМТ

Для быстрого старта с РМТ контентом используйте готовую конфигурацию:

```bash
# Копируем готовую РМТ конфигурацию
cp config.rmt.example .env

# Редактируем только токен и канал
nano .env
```

Готовая конфигурация включает:
- ✅ Real Person Fiction
- ✅ Fluff (милые работы)
- ✅ Angst (драматичные работы)
- ✅ Romance (романтические)
- ✅ Established Relationship (устоявшиеся отношения)

## Развертывание на Railway

### Быстрый старт

1. **Подключите GitHub репозиторий** к Railway
2. **Добавьте Redis сервис** в ваш проект
3. **Настройте переменные окружения**:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHANNEL_ID=your_channel_id_here
   REDIS_URL=redis://your-redis-url
   ```
4. **Деплой автоматически запустится**

### Подробная настройка

См. файл [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) для детальных инструкций.

### Railway CLI

```bash
# Установка Railway CLI
npm install -g @railway/cli

# Логин и подключение к проекту
railway login
railway link

# Деплой
railway up

# Просмотр логов
railway logs
```

## Структура проекта

```
RMT_AO3_RSS/
├── config.py                    # Конфигурация
├── pyproject.toml               # Конфигурация проекта и зависимости
├── uv.lock                      # Фиксированные версии зависимостей
├── Makefile                     # Команды для удобства разработки
├── README.md                    # Документация
├── main.py                      # Главный скрипт RSS парсера
├── rss_parser/                  # Парсер RSS лент
│   ├── __init__.py
│   └── rss_parser.py            # Основная логика парсинга RSS
├── telegram_bot/                # Работа с Telegram API
│   ├── __init__.py
│   ├── bot.py                   # Основная логика бота
│   ├── telegram_bot.py          # Класс для работы с Telegram API
│   ├── run_bot.py               # Скрипт запуска
│   └── test_bot.py              # Скрипт тестирования
├── scripts/                     # Вспомогательные скрипты
│   ├── setup.sh                 # Автоматическая настройка
│   ├── dev.sh                   # Режим разработки
│   └── format.sh                # Форматирование кода
└── bot_state.json               # Состояние бота (создается автоматически)
```

## Логирование

Бот ведет подробные логи:

- **Консоль**: Вывод в реальном времени
- **Файл**: `bot.log` - полная история работы
- **Уровни**: DEBUG, INFO, WARNING, ERROR

## Мониторинг

### Проверка работы

```bash
# Просмотр логов
tail -f bot.log

# Проверка состояния
cat bot_state.json
```

### Перезапуск

```bash
# Остановка (Ctrl+C)
# Запуск
uv run python telegram_bot/run_bot.py
# или
uv run rss-bot-run
```

## Устранение неполадок

### Частые проблемы

1. **"TELEGRAM_BOT_TOKEN не установлен"**
   - Проверьте файл `.env`
   - Убедитесь, что токен скопирован полностью

2. **"Нет доступа к каналу"**
   - Добавьте бота как администратора канала
   - Проверьте правильность ID канала

3. **"RSS лента пуста"**
   - Проверьте URL RSS ленты
   - Убедитесь, что лента доступна

4. **"Ошибка при получении RSS ленты"**
   - Проверьте интернет-соединение
   - Убедитесь, что URL корректный

### Отладка

```bash
# Запуск с подробными логами
LOG_LEVEL=DEBUG uv run python telegram_bot/test_bot.py
```

## Автоматический запуск

### Systemd (Linux)

Создайте файл `/etc/systemd/system/rss-bot.service`:

```ini
[Unit]
Description=RSS to Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/RMT
ExecStart=/path/to/uv run /path/to/RMT/run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
sudo systemctl enable rss-bot.service
sudo systemctl start rss-bot.service
```

### Docker

#### Быстрый запуск

```bash
# Сборка образа
make docker-build

# Запуск контейнера
make docker-run

# Или запуск в фоне
make docker-run-bg
```

#### Ручной запуск

```bash
# Сборка образа
docker build -t rmt-ao3-rss .

# Запуск контейнера
docker run --rm -it --name rmt-ao3-rss rmt-ao3-rss

# Или запуск в фоне
docker run -d --name rmt-ao3-rss rmt-ao3-rss
```

#### Конфигурация

1. Скопируйте `docker.env.example` в `.env`:
```bash
cp docker.env.example .env
```

2. Отредактируйте `.env` файл с вашими настройками:
```bash
# Redis настройки (внешний Redis)
REDIS_URL=redis://your-redis-host:6379

# Telegram настройки
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Настройки парсера
CHECK_INTERVAL_MINUTES=30
DAYS_TO_CHECK=3
LOG_LEVEL=INFO
```

3. Запуск с переменными окружения:
```bash
docker run --rm -it --env-file .env --name rmt-ao3-rss rmt-ao3-rss
```

#### Docker команды

```bash
make docker-build      # Сборка образа
make docker-run        # Запуск контейнера (интерактивно)
make docker-run-bg     # Запуск контейнера в фоне
make docker-stop       # Остановка контейнера
make docker-rm         # Удаление контейнера
make docker-logs       # Просмотр логов
make docker-shell      # Вход в контейнер
make docker-clean      # Очистка ресурсов
make docker-status      # Статус контейнера
```

#### Прямые Docker команды

```bash
# Сборка образа
docker build -t rmt-ao3-rss .

# Запуск с переменными окружения
docker run --rm -it --env-file .env --name rmt-ao3-rss rmt-ao3-rss

# Запуск в фоне
docker run -d --env-file .env --name rmt-ao3-rss rmt-ao3-rss

# Просмотр логов
docker logs -f rmt-ao3-rss

# Остановка
docker stop rmt-ao3-rss
```

## Лицензия

MIT License

## Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f bot.log`
2. Запустите тест: `python test_bot.py`
3. Проверьте конфигурацию в `.env`
