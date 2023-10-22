import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import psycopg2

# Состояния для конечного автомата
TRAIN_NUMBER, DEPARTURE_TIME, DEPARTURE, DESTINATION = range(4)

# Функция для начала ввода данных о поезде
def start(update, context):
    update.message.reply_text("Введите номер поезда:")
    return TRAIN_NUMBER

# Функция для сохранения данных о поезде в базу данных
def save_train_info(update, context):
    user_id = update.message.from_user.id
    train_number = context.user_data['train_number']
    departure_time = context.user_data['departure_time']
    departure = context.user_data['departure']
    destination = context.user_data['destination']

    conn = psycopg2.connect(database="trains", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trains (train_number, departure_time, departure, destination) VALUES (%s, %s, %s, %s)",
                   (train_number, departure_time, departure, destination))
    conn.commit()
    conn.close()

    update.message.reply_text(f"Информация о поезде {train_number} сохранена в базе данных.")
    context.user_data.clear()
    return ConversationHandler.END

# Функция для обработки ввода номера поезда
def input_train_number(update, context):
    user_data = context.user_data
    user_data['train_number'] = update.message.text
    update.message.reply_text("Введите время отправления (в формате ГГГГ-ММ-ДД ЧЧ:ММ):")
    return DEPARTURE_TIME

# Функция для обработки ввода времени отправления
def input_departure_time(update, context):
    user_data = context.user_data
    user_data['departure_time'] = update.message.text
    update.message.reply_text("Введите пункт отправления:")
    return DEPARTURE

# Функция для обработки ввода пункта отправления
def input_departure(update, context):
    user_data = context.user_data
    user_data['departure'] = update.message.text
    update.message.reply_text("Введите пункт назначения:")
    return DESTINATION

# Функция для обработки ввода пункта назначения
def input_destination(update, context):
    user_data = context.user_data
    user_data['destination'] = update.message.text

    update.message.reply_text("Пожалуй, проверьте введенные данные:\n"
                              f"Номер поезда: {user_data['train_number']}\n"
                              f"Время отправления: {user_data['departure_time']}\n"
                              f"Пункт отправления: {user_data['departure']}\n"
                              f"Пункт назначения: {user_data['destination']}\n"
                              "Если все верно, нажмите /save для сохранения, иначе, начните заново /start.")

    return ConversationHandler.END

# Функция для отмены ввода
def cancel(update, context):
    update.message.reply_text("Ввод данных отменен.")
    context.user_data.clear()
    return ConversationHandler.END

# Функция для просмотра данных
def view_data(update, context):
    conn = psycopg2.connect(database="trains", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trains")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        update.message.reply_text("В базе данных нет данных о поездах.")
    else:
        response = "Данные о поездах в базе данных:\n"
        for row in rows:
            response += f"Номер поезда: {row[1]}\nВремя отправления: {row[2]}\nПункт отправления: {row[3]}\nПункт назначения: {row[4]}\n\n"
        update.message.reply_text(response)

def main():
    updater = Updater(token="6079500895:AAGtu2k8sWrPrexqhuUqZz3g6lFLxgWIXLE", use_context=True)
    dp = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TRAIN_NUMBER: [MessageHandler(Filters.text & ~Filters.command, input_train_number)],
            DEPARTURE_TIME: [MessageHandler(Filters.text & ~Filters.command, input_departure_time)],
            DEPARTURE: [MessageHandler(Filters.text & ~Filters.command, input_departure)],
            DESTINATION: [MessageHandler(Filters.text & ~Filters.command, input_destination)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conversation_handler)
    dp.add_handler(CommandHandler('save', save_train_info))
    dp.add_handler(CommandHandler('view', view_data))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
