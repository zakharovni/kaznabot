#!/bin/bash
# Скрипт для остановки всех процессов бота

echo "Поиск процессов bot.py..."

# Находим все процессы Python, запущенные с bot.py
PIDS=$(ps aux | grep "[p]ython.*bot.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "Процессы бота не найдены."
else
    echo "Найдены процессы: $PIDS"
    for PID in $PIDS; do
        echo "Останавливаю процесс $PID..."
        kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
    done
    echo "Все процессы бота остановлены."
fi

# Также проверяем через lsof (если доступно)
if command -v lsof &> /dev/null; then
    echo ""
    echo "Проверка портов..."
    LSOF_PIDS=$(lsof -ti:8443 2>/dev/null)
    if [ ! -z "$LSOF_PIDS" ]; then
        echo "Найдены процессы на порту 8443: $LSOF_PIDS"
        for PID in $LSOF_PIDS; do
            kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        done
    fi
fi

echo "Готово!"
