#!/bin/bash
# Скрипт для резервного копирования базы данных

DB_FILE="income_bot.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/income_bot_${TIMESTAMP}.db"

# Создаем директорию для бэкапов
mkdir -p "$BACKUP_DIR"

if [ -f "$DB_FILE" ]; then
    echo "📦 Создание резервной копии базы данных..."
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "✅ Резервная копия создана: $BACKUP_FILE"
    echo ""
    echo "Размер файла:"
    ls -lh "$BACKUP_FILE"
else
    echo "❌ Файл базы данных не найден: $DB_FILE"
    exit 1
fi
