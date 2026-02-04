#!/bin/bash
# Скрипт для развертывания бота на сервере

set -e

echo "🚀 Развертывание бота для учета доходов..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3."
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден."
    echo ""
    echo "Для установки pip3 выполните одну из команд:"
    echo "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y python3-pip"
    echo "  CentOS/RHEL:   sudo yum install -y python3-pip"
    echo "  Fedora:        sudo dnf install -y python3-pip"
    echo ""
    echo "Или запустите скрипт установки:"
    echo "  sudo bash install-dependencies.sh"
    exit 1
fi

# Создаем виртуальное окружение (для Ubuntu 24.04+ требуется venv)
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip install -r requirements.txt

# Проверяем наличие config.py
if [ ! -f "config.py" ]; then
    echo "⚠️  Файл config.py не найден!"
    echo "📝 Создаю config.py из примера..."
    cp config.py.example config.py
    echo "⚠️  ВАЖНО: Отредактируйте config.py и добавьте ваш токен бота!"
    exit 1
fi

# Проверяем токен в config.py
if grep -q "YOUR_BOT_TOKEN" config.py; then
    echo "⚠️  ВАЖНО: Замените YOUR_BOT_TOKEN в config.py на ваш токен бота!"
    exit 1
fi

echo "✅ Развертывание завершено!"
echo ""
echo "Для запуска бота используйте один из способов:"
echo "1. systemd: sudo systemctl start income-bot"
echo "2. screen: screen -S bot python3 bot.py"
echo "3. tmux: tmux new -s bot python3 bot.py"
echo "4. Прямой запуск: python3 bot.py"
