#!/bin/bash
# Скрипт для полного удаления бота с сервера

set -e

echo "⚠️  ВНИМАНИЕ: Этот скрипт полностью удалит бота с сервера!"
echo ""
read -p "Вы уверены? Введите 'yes' для подтверждения: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено."
    exit 0
fi

echo ""
echo "🗑️  Удаление бота..."

# 1. Остановка и удаление systemd сервиса
if systemctl is-active --quiet income-bot 2>/dev/null; then
    echo "🛑 Остановка сервиса..."
    sudo systemctl stop income-bot
fi

if systemctl is-enabled --quiet income-bot 2>/dev/null; then
    echo "🔌 Отключение автозапуска..."
    sudo systemctl disable income-bot
fi

if [ -f /etc/systemd/system/income-bot.service ]; then
    echo "📄 Удаление service файла..."
    sudo rm /etc/systemd/system/income-bot.service
    sudo systemctl daemon-reload
fi

# 2. Остановка всех процессов бота
echo "🔪 Остановка всех процессов бота..."
sudo pkill -9 -f "bot.py" 2>/dev/null || true
sleep 2

# 3. Проверка, что процессов нет
if ps aux | grep -q "[b]ot.py"; then
    echo "⚠️  Предупреждение: Найдены процессы бота. Попробуйте остановить вручную."
    ps aux | grep "[b]ot.py"
else
    echo "✅ Все процессы остановлены"
fi

# 4. Создание резервной копии перед удалением
BOT_DIR="$HOME/kaznabot"
if [ -d "$BOT_DIR" ]; then
    echo ""
    echo "💾 Создание резервной копии перед удалением..."
    BACKUP_DIR="$HOME/kaznabot_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Копируем только важные файлы
    if [ -f "$BOT_DIR/income_bot.db" ]; then
        cp "$BOT_DIR/income_bot.db" "$BACKUP_DIR/"
        echo "✅ База данных сохранена в: $BACKUP_DIR"
    fi
    
    if [ -f "$BOT_DIR/config.py" ]; then
        cp "$BOT_DIR/config.py" "$BACKUP_DIR/"
        echo "✅ Конфигурация сохранена в: $BACKUP_DIR"
    fi
fi

# 5. Удаление директории бота
if [ -d "$BOT_DIR" ]; then
    echo ""
    read -p "Удалить директорию $BOT_DIR? (yes/no): " delete_dir
    if [ "$delete_dir" = "yes" ]; then
        echo "🗑️  Удаление директории бота..."
        rm -rf "$BOT_DIR"
        echo "✅ Директория удалена"
    else
        echo "📁 Директория сохранена: $BOT_DIR"
    fi
fi

# 6. Очистка временных файлов
echo ""
echo "🧹 Очистка временных файлов..."
rm -f /tmp/kaznabot*.tar.gz 2>/dev/null || true
rm -f /tmp/kaznabot_db.tar.gz 2>/dev/null || true

echo ""
echo "✅ Удаление завершено!"
echo ""
echo "📋 Что было сделано:"
echo "  - Сервис systemd остановлен и удален"
echo "  - Все процессы бота остановлены"
if [ -d "$BACKUP_DIR" ]; then
    echo "  - Резервная копия создана в: $BACKUP_DIR"
fi
if [ "$delete_dir" = "yes" ]; then
    echo "  - Директория бота удалена"
fi
echo ""
echo "💡 Если нужно восстановить данные, используйте файлы из резервной копии"
