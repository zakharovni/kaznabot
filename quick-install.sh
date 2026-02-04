#!/bin/bash
# Быстрая установка pip3 для разных дистрибутивов

echo "🔍 Определение системы..."

# Проверяем наличие разных пакетных менеджеров
if command -v apt-get &> /dev/null; then
    echo "📦 Обнаружен apt-get (Ubuntu/Debian)"
    echo "Установка pip3..."
    apt-get update
    apt-get install -y python3-pip python3-venv
    echo "✅ Готово!"
    
elif command -v dnf &> /dev/null; then
    echo "📦 Обнаружен dnf (Fedora)"
    echo "Установка pip3..."
    dnf install -y python3-pip
    echo "✅ Готово!"
    
elif command -v yum &> /dev/null; then
    echo "📦 Обнаружен yum (CentOS/RHEL)"
    echo "Установка pip3..."
    yum install -y python3-pip
    echo "✅ Готово!"
    
elif command -v apk &> /dev/null; then
    echo "📦 Обнаружен apk (Alpine)"
    echo "Установка pip3..."
    apk add --no-cache python3 py3-pip
    echo "✅ Готово!"
    
else
    echo "❌ Не удалось определить пакетный менеджер"
    echo ""
    echo "Попробуйте вручную:"
    echo "  apt-get install python3-pip  (Ubuntu/Debian)"
    echo "  dnf install python3-pip      (Fedora)"
    echo "  yum install python3-pip      (CentOS/RHEL)"
    echo "  apk add python3 py3-pip      (Alpine)"
    exit 1
fi

# Проверяем установку
if command -v pip3 &> /dev/null; then
    echo ""
    echo "✅ pip3 успешно установлен!"
    pip3 --version
else
    echo "❌ pip3 не установлен"
    exit 1
fi
