#!/bin/bash
# Скрипт для миграции бота на другой сервер

set -e

echo "🚀 Миграция бота на другой сервер"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -lt 1 ]; then
    echo -e "${RED}Использование:${NC}"
    echo "  $0 <новый_сервер> [пользователь]"
    echo ""
    echo "Примеры:"
    echo "  $0 192.168.1.100"
    echo "  $0 example.com root"
    echo "  $0 user@example.com"
    exit 1
fi

NEW_SERVER="$1"
NEW_USER="${2:-root}"

# Определяем текущую директорию
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CURRENT_DIR"

echo -e "${YELLOW}Текущий сервер:${NC} $(hostname)"
echo -e "${YELLOW}Новый сервер:${NC} $NEW_SERVER"
echo -e "${YELLOW}Пользователь:${NC} $NEW_USER"
echo ""

# Проверяем наличие базы данных
if [ ! -f "income_bot.db" ]; then
    echo -e "${RED}❌ База данных не найдена!${NC}"
    exit 1
fi

echo "📦 Шаг 1: Создание резервной копии базы данных..."
mkdir -p backups
BACKUP_FILE="backups/migration_$(date +%Y%m%d_%H%M%S).db"
cp income_bot.db "$BACKUP_FILE"
echo -e "${GREEN}✅ Резервная копия создана: $BACKUP_FILE${NC}"

echo ""
echo "📤 Шаг 2: Копирование файлов на новый сервер..."
echo "Директория назначения: /root/kaznabot (или ~/kaznabot)"

# Создаем временный архив
TEMP_ARCHIVE="/tmp/kaznabot_migration_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "Создание архива..."

# Исключаем ненужные файлы
tar --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='backups' \
    -czf "$TEMP_ARCHIVE" .

echo "Копирование архива на новый сервер..."
scp "$TEMP_ARCHIVE" "$NEW_USER@$NEW_SERVER:/tmp/"

echo "Распаковка на новом сервере..."
ssh "$NEW_USER@$NEW_SERVER" << EOF
    # Создаем директорию
    mkdir -p ~/kaznabot
    cd ~/kaznabot
    
    # Распаковываем архив
    tar -xzf $(basename $TEMP_ARCHIVE) -C .
    
    # Удаляем архив
    rm $(basename $TEMP_ARCHIVE)
    
    # Копируем базу данных
    echo "Копирование базы данных..."
EOF

# Копируем базу данных отдельно
echo "Копирование базы данных..."
scp income_bot.db "$NEW_USER@$NEW_SERVER:~/kaznabot/"

echo ""
echo -e "${GREEN}✅ Файлы скопированы!${NC}"

echo ""
echo "🔧 Шаг 3: Настройка на новом сервере..."
ssh "$NEW_USER@$NEW_SERVER" << 'ENDSSH'
    cd ~/kaznabot
    
    echo "Проверка Python..."
    if ! command -v python3 &> /dev/null; then
        echo "Установка Python3..."
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    fi
    
    echo "Создание виртуального окружения..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    echo "Установка зависимостей..."
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    
    echo "Проверка config.py..."
    if [ ! -f "config.py" ]; then
        echo "⚠️  ВНИМАНИЕ: Создайте config.py с токеном бота!"
        cp config.py.example config.py
    fi
    
    echo "Настройка systemd..."
    if [ -f "quick-setup-systemd.sh" ]; then
        sudo bash quick-setup-systemd.sh
    fi
    
    echo ""
    echo "✅ Настройка завершена!"
ENDSSH

echo ""
echo -e "${GREEN}✅ Миграция завершена!${NC}"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. На новом сервере проверьте config.py:"
echo "   ssh $NEW_USER@$NEW_SERVER"
echo "   cd ~/kaznabot"
echo "   nano config.py  # Убедитесь, что токен правильный"
echo ""
echo "2. Запустите бота на новом сервере:"
echo "   sudo systemctl start income-bot"
echo "   sudo systemctl enable income-bot"
echo "   sudo systemctl status income-bot"
echo ""
echo "3. Проверьте работу бота в Telegram"
echo ""
echo "4. После проверки остановите бота на старом сервере:"
echo "   sudo systemctl stop income-bot"
echo "   sudo systemctl disable income-bot"
echo ""
echo "5. Удалите временный архив:"
echo "   rm $TEMP_ARCHIVE"
