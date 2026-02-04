#!/bin/bash
# Быстрая установка systemd сервиса

set -e

CURRENT_USER=$(whoami)
WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Быстрая установка systemd сервиса..."
echo "Пользователь: $CURRENT_USER"
echo "Директория: $WORK_DIR"

# Проверяем наличие venv
if [ ! -d "$WORK_DIR/venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    exit 1
fi

# Создаем service файл напрямую
SERVICE_CONTENT="[Unit]
Description=Income Bot - Telegram бот для учета доходов
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$WORK_DIR
ExecStart=$WORK_DIR/venv/bin/python $WORK_DIR/bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=income-bot

[Install]
WantedBy=multi-user.target"

echo "📝 Создание service файла..."
echo "$SERVICE_CONTENT" | sudo tee /etc/systemd/system/income-bot.service > /dev/null

echo "🔄 Перезагрузка systemd..."
sudo systemctl daemon-reload

echo "✅ Сервис установлен!"
echo ""
echo "Теперь можно запустить:"
echo "  sudo systemctl start income-bot"
echo "  sudo systemctl enable income-bot"
echo "  sudo systemctl status income-bot"
