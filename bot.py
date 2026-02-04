import logging
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Conflict, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from dateutil import parser as date_parser
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Уменьшаем уровень логирования для httpx (меньше шума от сетевых запросов)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Подавляем предупреждения о per_message в ConversationHandler
logging.getLogger('telegram.ext._conversationhandler').setLevel(logging.ERROR)

# Состояния для ConversationHandler
WAITING_AMOUNT, WAITING_DATE, WAITING_CATEGORY_NAME = range(3)

# Инициализация базы данных
db = Database()


def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton("🗑️ Удалить запись", callback_data="delete")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categories_keyboard(user_id: int, include_add_category: bool = True):
    """Клавиатура с категориями"""
    categories = db.get_categories(user_id)
    keyboard = []
    
    # Кнопки категорий по 2 в ряд
    for i in range(0, len(categories), 2):
        row = []
        row.append(InlineKeyboardButton(categories[i], callback_data=f"category_{categories[i]}"))
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"category_{categories[i + 1]}"))
        keyboard.append(row)
    
    # Кнопка добавления категории
    if include_add_category:
        keyboard.append([InlineKeyboardButton("➕ Добавить категорию", callback_data="add_category")])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)


def get_statistics_keyboard():
    """Клавиатура статистики"""
    keyboard = [
        [InlineKeyboardButton("📅 По месяцам", callback_data="stats_monthly")],
        [InlineKeyboardButton("📈 Всего", callback_data="stats_all")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_months_keyboard():
    """Клавиатура выбора месяца"""
    current_date = datetime.now()
    keyboard = []
    
    # Показываем последние 6 месяцев
    for i in range(6):
        month_date = current_date.replace(day=1)
        for _ in range(i):
            if month_date.month == 1:
                month_date = month_date.replace(year=month_date.year - 1, month=12)
            else:
                month_date = month_date.replace(month=month_date.month - 1)
        
        month_name = month_date.strftime("%B %Y")
        callback_data = f"month_{month_date.year}_{month_date.month}"
        keyboard.append([InlineKeyboardButton(month_name, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="statistics")])
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_text(user_id: int) -> str:
    """Получить текст главного меню со статистикой"""
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Получаем сумму за текущий месяц (начиная с января 2026)
    month_total = 0.0
    if current_year >= 2026:
        month_total = db.get_month_total(user_id, current_year, current_month)
    
    # Получаем общую сумму за все время
    total_amount = db.get_total_amount(user_id)
    
    # Название месяца на русском
    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    month_name = month_names.get(current_month, "")
    
    text = (
        f"📊 <b>Главное меню</b>\n\n"
        f"📅 За {month_name} {current_year}: <b>{month_total:,.2f} ₽</b>\n"
        f"💰 Итого за все время: <b>{total_amount:,.2f} ₽</b>\n\n"
        f"Выберите действие:"
    )
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    menu_text = get_main_menu_text(user_id)
    
    await update.message.reply_text(
        menu_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data

    if data == "add":
        # Очищаем данные пользователя при возврате к выбору категории
        context.user_data.clear()
        await query.edit_message_text(
            "Выберите категорию:",
            reply_markup=get_categories_keyboard(user_id)
        )
        return ConversationHandler.END
    
    elif data == "statistics":
        await query.edit_message_text(
            "Выберите тип статистики:",
            reply_markup=get_statistics_keyboard()
        )
    
    elif data == "back_to_main":
        # Очищаем данные пользователя при возврате в главное меню
        context.user_data.clear()
        menu_text = get_main_menu_text(user_id)
        await query.edit_message_text(
            menu_text,
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    elif data == "add_category":
        await query.edit_message_text(
            "Введите название новой категории:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Отмена", callback_data="add")
            ]])
        )
        return WAITING_CATEGORY_NAME
    
    elif data.startswith("category_"):
        category_name = data.replace("category_", "")
        context.user_data['selected_category'] = category_name
        await query.edit_message_text(
            f"Категория: <b>{category_name}</b>\n\n"
            "Введите сумму дохода:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data="add")
            ]])
        )
        return WAITING_AMOUNT
    
    elif data == "stats_monthly":
        await query.edit_message_text(
            "Выберите месяц:",
            reply_markup=get_months_keyboard()
        )
    
    elif data.startswith("month_"):
        parts = data.replace("month_", "").split("_")
        year = int(parts[0])
        month = int(parts[1])
        stats = db.get_monthly_statistics(user_id, year, month)
        
        if not stats:
            text = f"📅 Статистика за {datetime(year, month, 1).strftime('%B %Y')}\n\nНет данных за этот период."
        else:
            total = sum(amount for _, amount in stats)
            text = f"📅 Статистика за {datetime(year, month, 1).strftime('%B %Y')}\n\n"
            for category, amount in stats:
                percentage = (amount / total * 100) if total > 0 else 0
                text += f"<b>{category}</b>: {amount:,.2f} ₽ ({percentage:.1f}%)\n"
            text += f"\n<b>Итого:</b> {total:,.2f} ₽"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_months_keyboard()
        )
    
    elif data == "stats_all":
        stats = db.get_all_statistics(user_id)
        total = db.get_total_amount(user_id)
        
        if not stats:
            text = "📈 Общая статистика\n\nНет данных."
        else:
            text = "📈 Общая статистика\n\n"
            for category, amount in stats:
                percentage = (amount / total * 100) if total > 0 else 0
                text += f"<b>{category}</b>: {amount:,.2f} ₽ ({percentage:.1f}%)\n"
            text += f"\n<b>Итого:</b> {total:,.2f} ₽"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_statistics_keyboard()
        )
    
    elif data == "delete":
        transactions = db.get_recent_transactions(user_id, limit=10)
        
        if not transactions:
            await query.edit_message_text(
                "🗑️ Удаление записей\n\nНет записей для удаления.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
                ]])
            )
        else:
            text = "🗑️ Выберите запись для удаления:\n\n"
            keyboard = []
            
            for i, (trans_id, category, amount, trans_date) in enumerate(transactions[:10], 1):
                date_obj = datetime.strptime(trans_date, "%Y-%m-%d").date()
                text += f"{i}. {category}: {amount:,.2f} ₽ ({date_obj.strftime('%d.%m.%Y')})\n"
                keyboard.append([InlineKeyboardButton(
                    f"🗑️ {category} - {amount:,.2f} ₽",
                    callback_data=f"delete_{trans_id}"
                )])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif data.startswith("delete_"):
        transaction_id = int(data.replace("delete_", ""))
        transaction = db.get_transaction(transaction_id, user_id)
        
        if not transaction:
            await query.answer("Запись не найдена!", show_alert=True)
            return ConversationHandler.END
        
        trans_id, category, amount, trans_date = transaction
        date_obj = datetime.strptime(trans_date, "%Y-%m-%d").date()
        
        # Показываем подтверждение удаления
        await query.edit_message_text(
            f"⚠️ Подтвердите удаление:\n\n"
            f"Категория: <b>{category}</b>\n"
            f"Сумма: <b>{amount:,.2f} ₽</b>\n"
            f"Дата: <b>{date_obj.strftime('%d.%m.%Y')}</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{trans_id}")],
                [InlineKeyboardButton("❌ Отмена", callback_data="delete")]
            ])
        )
    
    elif data.startswith("confirm_delete_"):
        transaction_id = int(data.replace("confirm_delete_", ""))
        transaction = db.get_transaction(transaction_id, user_id)
        
        if transaction and db.delete_transaction(transaction_id, user_id):
            trans_id, category, amount, trans_date = transaction
            date_obj = datetime.strptime(trans_date, "%Y-%m-%d").date()
            
            menu_text = get_main_menu_text(user_id)
            await query.edit_message_text(
                f"✅ Запись удалена!\n\n"
                f"Категория: <b>{category}</b>\n"
                f"Сумма: <b>{amount:,.2f} ₽</b>\n"
                f"Дата: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
                f"{menu_text}",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
        else:
            await query.answer("Ошибка при удалении записи!", show_alert=True)
            menu_text = get_main_menu_text(user_id)
            await query.edit_message_text(
                menu_text,
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
    
    return ConversationHandler.END


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода суммы"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        if amount <= 0:
            await update.message.reply_text(
                "Сумма должна быть положительным числом. Попробуйте еще раз:"
            )
            return WAITING_AMOUNT
        
        context.user_data['amount'] = amount
        category_name = context.user_data.get('selected_category', '')
        
        await update.message.reply_text(
            f"Сумма: <b>{amount:,.2f} ₽</b>\n"
            f"Категория: <b>{category_name}</b>\n\n"
            "Введите дату (ДД.ММ.ГГГГ) или отправьте 'сегодня' для сегодняшней даты:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Отмена", callback_data="add")
            ]])
        )
        return WAITING_DATE
    
    except ValueError:
        await update.message.reply_text(
            "Неверный формат суммы. Введите число (например: 1000 или 1000.50):"
        )
        return WAITING_AMOUNT


async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода даты"""
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    
    try:
        if text == 'сегодня' or text == 'today':
            transaction_date = date.today()
        else:
            # Пробуем разные форматы даты
            try:
                transaction_date = date_parser.parse(text, dayfirst=True).date()
            except:
                # Пробуем формат ДД.ММ.ГГГГ
                transaction_date = datetime.strptime(text, "%d.%m.%Y").date()
        
        amount = context.user_data.get('amount')
        category_name = context.user_data.get('selected_category')
        
        if db.add_transaction(user_id, category_name, amount, transaction_date.isoformat()):
            total = db.get_total_by_category(user_id, category_name)
            await update.message.reply_text(
                f"✅ Доход добавлен!\n\n"
                f"Категория: <b>{category_name}</b>\n"
                f"Сумма: <b>{amount:,.2f} ₽</b>\n"
                f"Дата: <b>{transaction_date.strftime('%d.%m.%Y')}</b>\n\n"
                f"Всего по категории: <b>{total:,.2f} ₽</b>",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
            
            # Очищаем данные
            context.user_data.clear()
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ Ошибка при добавлении дохода. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ (например: 01.02.2026) или 'сегодня':"
        )
        return WAITING_DATE


async def handle_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик добавления новой категории"""
    user_id = update.effective_user.id
    category_name = update.message.text.strip().upper()
    
    if len(category_name) == 0:
        await update.message.reply_text(
            "Название категории не может быть пустым. Попробуйте еще раз:"
        )
        return WAITING_CATEGORY_NAME
    
    if db.add_category(user_id, category_name):
        await update.message.reply_text(
            f"✅ Категория <b>{category_name}</b> добавлена!",
            parse_mode='HTML',
            reply_markup=get_categories_keyboard(user_id)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"❌ Категория <b>{category_name}</b> уже существует или произошла ошибка.",
            parse_mode='HTML',
            reply_markup=get_categories_keyboard(user_id)
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    context.user_data.clear()
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


def clear_webhook_sync(bot_token: str):
    """Очистить webhook перед запуском polling (синхронный метод)"""
    import requests
    try:
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        params = {"drop_pending_updates": True}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            logger.info("Webhook очищен успешно")
        else:
            logger.warning(f"Не удалось очистить webhook: {response.status_code}")
    except Exception as e:
        logger.warning(f"Не удалось очистить webhook: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    error = context.error
    
    # Игнорируем временные сетевые ошибки (они обрабатываются автоматически)
    if isinstance(error, NetworkError):
        # Логируем только если это не временная ошибка подключения
        error_msg = str(error)
        if "ConnectError" in error_msg or "TimeoutError" in error_msg:
            logger.debug(f"Временная сетевая ошибка (автоматически обрабатывается): {error}")
        else:
            logger.warning(f"Сетевая ошибка: {error}")
        return
    
    # Остальные ошибки логируем полностью
    if isinstance(error, Conflict):
        logger.error("⚠️  КОНФЛИКТ: Запущен другой экземпляр бота! Остановите все другие процессы бота.")
        logger.error("Попробуйте найти процессы: lsof -i :8443 или проверьте другие терминалы/окна")
    else:
        logger.error(f"Ошибка при обработке обновления: {error}", exc_info=error)


def main():
    """Главная функция запуска бота"""
    from config import BOT_TOKEN
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("⚠️  ВНИМАНИЕ: Замените YOUR_BOT_TOKEN в config.py на ваш токен бота!")
        return
    
    # Очищаем webhook перед запуском (синхронно)
    clear_webhook_sync(BOT_TOKEN)
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler для добавления дохода
    add_income_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^category_")],
        states={
            WAITING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount),
                CallbackQueryHandler(button_handler, pattern="^(add|back_to_main)$")
            ],
            WAITING_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date),
                CallbackQueryHandler(button_handler, pattern="^(add|back_to_main)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
    )
    
    # ConversationHandler для добавления категории
    add_category_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^add_category$")],
        states={
            WAITING_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_name),
                CallbackQueryHandler(button_handler, pattern="^(add|back_to_main)$")
            ],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^(add|back_to_main)$")],
        per_chat=True,
        per_user=True,
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_income_handler)
    application.add_handler(add_category_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Conflict as e:
        logger.error("⚠️  КОНФЛИКТ: Запущен другой экземпляр бота!")
        logger.error("Остановите все другие процессы бота перед запуском.")
        logger.error("Попробуйте найти процессы командой: lsof -i :8443")
        logger.error("Или проверьте другие терминалы/окна, где может быть запущен бот.")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)


if __name__ == '__main__':
    main()
