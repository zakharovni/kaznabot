# Инструкция по миграции бота на другой сервер

## Быстрая миграция (автоматическая)

### На старом сервере:

```bash
cd ~/kaznabot
git pull  # Обновите код, чтобы получить migrate-server.sh

# Запустите скрипт миграции
./migrate-server.sh <новый_сервер> [пользователь]
```

**Примеры:**
```bash
# С IP адресом
./migrate-server.sh 192.168.1.100

# С доменным именем
./migrate-server.sh example.com

# С указанием пользователя
./migrate-server.sh example.com myuser

# С полным путем SSH
./migrate-server.sh user@example.com
```

## Ручная миграция (пошагово)

### Шаг 1: Резервное копирование на старом сервере

```bash
cd ~/kaznabot

# Создайте резервную копию базы данных
./backup-db.sh

# Или вручную
mkdir -p backups
cp income_bot.db backups/backup_$(date +%Y%m%d_%H%M%S).db
```

### Шаг 2: Подготовка на новом сервере

```bash
# Подключитесь к новому серверу
ssh user@новый_сервер

# Установите зависимости
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Клонируйте репозиторий (или создайте директорию)
git clone git@github.com:zakharovni/kaznabot.git
# ИЛИ
mkdir -p ~/kaznabot
cd ~/kaznabot
```

### Шаг 3: Копирование файлов

**Вариант A: Через SCP (если нет Git)**

```bash
# С старого сервера
cd ~/kaznabot
tar --exclude='venv' --exclude='__pycache__' --exclude='.git' \
    -czf /tmp/kaznabot.tar.gz .
scp /tmp/kaznabot.tar.gz user@новый_сервер:/tmp/
scp income_bot.db user@новый_сервер:~/kaznabot/

# На новом сервере
cd ~/kaznabot
tar -xzf /tmp/kaznabot.tar.gz
```

**Вариант B: Через Git (рекомендуется)**

```bash
# На новом сервере
git clone git@github.com:zakharovni/kaznabot.git
cd kaznabot

# Скопируйте только базу данных со старого сервера
scp user@старый_сервер:~/kaznabot/income_bot.db .
```

### Шаг 4: Настройка на новом сервере

```bash
cd ~/kaznabot

# Создайте config.py с токеном
cp config.py.example config.py
nano config.py  # Добавьте токен бота

# Развертывание
./deploy.sh

# Настройка systemd
sudo bash quick-setup-systemd.sh

# Запуск
sudo systemctl start income-bot
sudo systemctl enable income-bot
sudo systemctl status income-bot
```

### Шаг 5: Проверка работы

```bash
# Проверьте логи
sudo journalctl -u income-bot -f

# Проверьте в Telegram - отправьте /start боту
```

### Шаг 6: Остановка на старом сервере

```bash
# На старом сервере
sudo systemctl stop income-bot
sudo systemctl disable income-bot

# Опционально: удалите файлы
# rm -rf ~/kaznabot
```

## Важные моменты

1. **База данных** - обязательно скопируйте `income_bot.db` со старого сервера
2. **Токен бота** - должен быть одинаковым на обоих серверах (или создайте нового бота)
3. **Не запускайте бота одновременно** на двух серверах - будет конфликт
4. **Проверьте работу** на новом сервере перед остановкой старого

## Устранение проблем

### Конфликт при запуске

Если видите ошибку "Conflict: terminated by other getUpdates request":

```bash
# Остановите бота на старом сервере
ssh старый_сервер
sudo systemctl stop income-bot

# Перезапустите на новом
sudo systemctl restart income-bot
```

### База данных не скопировалась

```bash
# Скопируйте вручную
scp user@старый_сервер:~/kaznabot/income_bot.db ~/kaznabot/

# Восстановите
./restore-db.sh income_bot.db
```

### Проблемы с правами доступа

```bash
# Установите правильные права
chmod 644 income_bot.db
chown $USER:$USER income_bot.db
```
