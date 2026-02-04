# Инструкция по развертыванию бота на сервере

## Подготовка сервера

### 1. Установка зависимостей системы

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip git

# CentOS/RHEL
sudo yum install python3 python3-pip git
```

### 2. Загрузка проекта на сервер

#### Вариант A: Через Git (если проект в репозитории)
```bash
git clone <ваш-репозиторий> KaznaBot
cd KaznaBot
```

#### Вариант B: Через SCP (прямая загрузка)
```bash
# С вашего компьютера
scp -r KaznaBot user@your-server:/path/to/destination/
ssh user@your-server
cd /path/to/destination/KaznaBot
```

#### Вариант C: Через rsync
```bash
rsync -avz KaznaBot/ user@your-server:/path/to/KaznaBot/
```

## Развертывание

### Шаг 1: Настройка конфигурации

```bash
cd KaznaBot
cp config.py.example config.py
nano config.py  # или используйте ваш любимый редактор
```

Добавьте ваш токен бота в `config.py`:
```python
BOT_TOKEN = "ваш_токен_здесь"
```

### Шаг 2: Установка зависимостей

```bash
chmod +x deploy.sh
./deploy.sh
```

Или вручную:
```bash
pip3 install -r requirements.txt
```

### Шаг 3: Тестовый запуск

Проверьте, что бот работает:
```bash
python3 bot.py
```

Если все работает, остановите бота (Ctrl+C) и переходите к следующему шагу.

## Варианты запуска на сервере

### Вариант 1: Systemd Service (Рекомендуется)

1. Отредактируйте файл `income-bot.service`:
```bash
nano income-bot.service
```

Измените:
- `YOUR_USER` на имя вашего пользователя
- `/path/to/KaznaBot` на реальный путь к проекту

2. Установите service:
```bash
sudo cp income-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable income-bot
sudo systemctl start income-bot
```

3. Проверьте статус:
```bash
sudo systemctl status income-bot
```

4. Просмотр логов:
```bash
sudo journalctl -u income-bot -f
```

### Вариант 2: Screen

```bash
screen -S bot
cd /path/to/KaznaBot
python3 bot.py
# Нажмите Ctrl+A, затем D для отсоединения
```

Вернуться к сессии:
```bash
screen -r bot
```

### Вариант 3: Tmux

```bash
tmux new -s bot
cd /path/to/KaznaBot
python3 bot.py
# Нажмите Ctrl+B, затем D для отсоединения
```

Вернуться к сессии:
```bash
tmux attach -t bot
```

### Вариант 4: nohup (простой вариант)

```bash
cd /path/to/KaznaBot
nohup python3 bot.py > bot.log 2>&1 &
```

Просмотр логов:
```bash
tail -f bot.log
```

Остановка:
```bash
pkill -f "python3 bot.py"
```

## Обновление бота

### Если используете Git:
```bash
cd /path/to/KaznaBot
git pull
sudo systemctl restart income-bot  # если используете systemd
```

### Если загружаете файлы вручную:
```bash
# Остановите бота
sudo systemctl stop income-bot  # или pkill -f "python3 bot.py"

# Загрузите новые файлы
# Запустите снова
sudo systemctl start income-bot
```

## Мониторинг и логи

### Systemd:
```bash
# Статус
sudo systemctl status income-bot

# Логи
sudo journalctl -u income-bot -f

# Последние 100 строк логов
sudo journalctl -u income-bot -n 100
```

### Ручной запуск:
```bash
# Логи в файл
python3 bot.py >> bot.log 2>&1

# Просмотр логов
tail -f bot.log
```

## Безопасность

1. **Не коммитьте config.py в Git**
   - Убедитесь, что `config.py` в `.gitignore`
   - Используйте `config.py.example` как шаблон

2. **Права доступа**
   ```bash
   chmod 600 config.py  # Только владелец может читать/писать
   ```

3. **Firewall**
   - Бот не требует входящих подключений
   - Убедитесь, что исходящие подключения разрешены (для API Telegram)

## Устранение неполадок

### Бот не запускается:
```bash
# Проверьте логи
sudo journalctl -u income-bot -n 50

# Проверьте токен
cat config.py | grep BOT_TOKEN

# Проверьте Python и зависимости
python3 --version
pip3 list | grep python-telegram-bot
```

### Бот падает:
```bash
# Проверьте права доступа к базе данных
ls -la income_bot.db

# Проверьте место на диске
df -h
```

### Конфликт (несколько экземпляров):
```bash
# Найдите все процессы
ps aux | grep bot.py

# Остановите все
pkill -f "python3 bot.py"

# Запустите заново
sudo systemctl start income-bot
```

## Резервное копирование

Рекомендуется регулярно делать резервные копии базы данных:

```bash
# Создать backup
cp income_bot.db backups/income_bot_$(date +%Y%m%d_%H%M%S).db

# Автоматический backup (добавьте в crontab)
# 0 2 * * * cp /path/to/KaznaBot/income_bot.db /path/to/backups/income_bot_$(date +\%Y\%m\%d).db
```

## Контакты и поддержка

При возникновении проблем проверьте:
1. Логи бота
2. Статус сервиса
3. Сетевое подключение
4. Токен бота
