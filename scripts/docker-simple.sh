#!/bin/bash

# Простой скрипт для работы с Docker контейнером RSS парсера

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен"
        exit 1
    fi
}

# Сборка образа
build() {
    log "Сборка Docker образа..."
    docker build -t rmt-ao3-rss .
    success "Образ собран успешно"
}

# Запуск контейнера
run() {
    local mode=${1:-interactive}
    
    if [ "$mode" = "background" ]; then
        log "Запуск контейнера в фоне..."
        docker run -d --name rmt-ao3-rss rmt-ao3-rss
        success "Контейнер запущен в фоне"
        log "Для просмотра логов: docker logs -f rmt-ao3-rss"
    else
        log "Запуск контейнера в интерактивном режиме..."
        docker run --rm -it --name rmt-ao3-rss rmt-ao3-rss
    fi
}

# Остановка контейнера
stop() {
    log "Остановка контейнера..."
    docker stop rmt-ao3-rss || true
    success "Контейнер остановлен"
}

# Удаление контейнера
rm() {
    log "Удаление контейнера..."
    docker rm rmt-ao3-rss || true
    success "Контейнер удален"
}

# Просмотр логов
logs() {
    log "Просмотр логов контейнера..."
    docker logs -f rmt-ao3-rss
}

# Вход в контейнер
shell() {
    log "Вход в контейнер..."
    docker exec -it rmt-ao3-rss /bin/bash
}

# Очистка
clean() {
    log "Очистка Docker ресурсов..."
    docker stop rmt-ao3-rss || true
    docker rm rmt-ao3-rss || true
    docker rmi rmt-ao3-rss || true
    success "Очистка завершена"
}

# Проверка статуса
status() {
    log "Проверка статуса контейнера..."
    if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q rmt-ao3-rss; then
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep rmt-ao3-rss
    else
        warning "Контейнер rmt-ao3-rss не найден"
    fi
}

# Показать справку
help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  build           - Собрать Docker образ"
    echo "  run             - Запустить контейнер (интерактивно)"
    echo "  run-bg          - Запустить контейнер в фоне"
    echo "  stop            - Остановить контейнер"
    echo "  rm              - Удалить контейнер"
    echo "  logs            - Показать логи"
    echo "  shell           - Войти в контейнер"
    echo "  clean           - Очистить Docker ресурсы"
    echo "  status          - Показать статус контейнера"
    echo "  help            - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  $0 run-bg"
    echo "  $0 logs"
}

# Основная логика
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        run)
            run interactive
            ;;
        run-bg)
            run background
            ;;
        stop)
            stop
            ;;
        rm)
            rm
            ;;
        logs)
            logs
            ;;
        shell)
            shell
            ;;
        clean)
            clean
            ;;
        status)
            status
            ;;
        help|--help|-h)
            help
            ;;
        *)
            error "Неизвестная команда: $1"
            help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
