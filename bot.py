from telegram import Update,ReplyKeyboardMarkup,ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,MessageHandler,filters,CallbackContext
import requests
import re

TOKEN='YOU_TOKEN'
API_URL = 'http://localhost:8000'  # адрес вашего FastAPI приложения


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['Создать мероприятие'],
        ['Завершить мероприятие'],
        ['Показать все мероприятия'],
        ['Показать ближайшее мероприятие'],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)


class States:
    WAITING_FOR_NAME_EVENT = "waiting_for_name_event"
    WAITING_NAME_FOR_END= "waiting_name_for_end"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    state = context.user_data.get('state')
    if text == 'Создать мероприятие':
        await update.message.reply_text("Пожалуйста, введите название и дату мероприятия(в формате число.месяц):")
        context.user_data['state'] = States.WAITING_FOR_NAME_EVENT
    elif text == 'Завершить мероприятие':
        await update.message.reply_text("Пожалуйста, введите название мероприятия:")
        context.user_data['state'] = States.WAITING_NAME_FOR_END
    elif text == 'Показать все мероприятия':
        await view_events(update,context)
    elif text == 'Показать ближайшее мероприятие':
        await view_last_event(update,context)
    elif state == States.WAITING_NAME_FOR_END:
        await close_events(update, context)
    elif state == States.WAITING_FOR_NAME_EVENT:
        await create_event(update, context)


async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    result = message_text.split()
    if len(result) < 3:
        await update.message.reply_text("Не все данные введены.")
    if result[0].isalpha():
        name = result[0]
    else:
        await update.message.reply_text("Название не может иметь цифры")
    date = result[1]
    pattern = r'^[0-9.]+$'  # Регулярное выражение для проверки
    if not re.match(pattern, date):
        await update.message.reply_text("Дата должна состоять только из цифр и точки.")
        return
        
    description = "".join(result[2])
    
    # Подготовляем данные для отправки
    event_data = {
        "name": name,
        "date": date,
        "description": description
    }
    print(event_data)
    # Отправка POST-запроса
    try:
        response = requests.post(f"{API_URL}/create_events/", json=event_data)
        response_data = response.json()

        if response.status_code == 200:
            await update.message.reply_text(response_data.get("message", "Событие создано успешно!"))
        else:
            await update.message.reply_text(f"Ошибка при создании события: {response_data.get('error', 'Неизвестная ошибка')}")
    except Exception as e:
        await update.message.reply_text(f"Не удалось связаться с API: {str(e)}")
    context.user_data['state'] = None



async def close_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_name=update.message.text
    response = requests.delete(f"{API_URL}/close_events/{event_name}",json={"name":event_name})
    if response.ok:
        result = response.json()
        await update.message.reply_text(result.get("message"))
    context.user_data['state'] = None


    


async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(f"{API_URL}/view_events/")
    if response.status_code == 200:
        events = response.json()        
        # Предполагается, что events - это список событий
        if events:
            events_list = "".join([f"Название: {event['name']};   Дата: {event['date']};   Описание: {event['description']}; \n" for event in events.values()])
            await update.message.reply_text(f"Мероприятия:\n{events_list}")
        else:
            await update.message.reply_text("Нет мероприятий для отображения.")
    else:
        await update.message.reply_text("Ошибка при получении данных!")



async def view_last_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(f"{API_URL}/last_event/")
    if response.status_code == 200:
        last_event = response.json()
        
        if 'error' not in last_event:
            await update.message.reply_text(f"Последнее мероприятие:\n"
                                             f"Название: {last_event['name']}\n"
                                             f"Дата: {last_event['date']}\n"
                                             f"Описание: {last_event['description']}\n")
        else:
            await update.message.reply_text("Нет мероприятий для отображения.")
    else:
        await update.message.reply_text("Ошибка при получении данных!")

# Реализация обработчиков для создания, обновления и удаления мероприятий

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create", create_event))
    app.add_handler(CommandHandler("close", close_events))
    app.add_handler(CommandHandler("view", view_events))
    app.add_handler(CommandHandler("last", view_last_event))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



    # Добавьте обработчики для update и delete здесь
    app.run_polling()

if __name__ == '__main__':
    main()
