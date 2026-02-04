#!/bin/bash
# Скрипт для установки зависимостей на сервере

set -e

echo "🔍 Определение дистрибутива Linux..."

# Определяем дистрибутив
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Не удалось определить дистрибутив"
    exit 1
fi

echo "📦 Дистрибутив: $OS"

# Установка pip3 в зависимости от дистрибутива
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo "📥 Установка pip3 для Ubuntu/Debian..."
    apt-get update
    apt-get install -y python3-pip python3-venv
    
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    echo "📥 Установка pip3 для CentOS/RHEL/Fedora..."
    if command -v dnf &> /dev/null; then
        dnf install -y python3-pip
    else
        yum install -y python3-pip
    fi
    
elif [ "$OS" = "alpine" ]; then
    echo "📥 Установка pip3 для Alpine Linux..."
    apk add --no-cache python3 py3-pip
    
else
    echo "⚠️  Неизвестный дистрибутив. Попробуйте установить pip3 вручную:"
    echo "   Ubuntu/Debian: apt-get install python3-pip"
    echo "   CentOS/RHEL: yum install python3-pip"
    echo "   Fedora: dnf install python3-pip"
    exit 1
fi

# Проверяем установку
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 успешно установлен!"
    pip3 --version
else
    echo "❌ pip3 не установлен. Попробуйте установить вручную."
    exit 1
fi

echo ""
echo "✅ Зависимости установлены. Теперь можно запустить deploy.sh"
