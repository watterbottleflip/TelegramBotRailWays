import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher(bot, storage=MemoryStorage())

class TrainInfoForm(StatesGroup):
    TRAIN_NUMBER = State()
    DEPARTURE_TIME = State()
    DEPARTURE = State()
    DESTINATION = State()
    DELETE_CONFIRM = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(f"Здравствуйте! Этот бот🤖 позволяет записывать данные о ваших железнодорожных путях\nДоступные команды:\n"
                        f"ℹ️/start_to_save - для старта записи\n"
                        f"️👁️/view - для просмотра сохраненных записей\n"
                        f"🗑️/delete - для удаления сохраненных записей\n"
                        f"🚫/cancel - для прерывания любого действия"
                        )
    

@dp.message_handler(commands=['start_to_save'])
async def start_to_save(message: types.Message):
    await message.reply("Для отмены текущего действия используйте /cancel.")
    await message.reply("🚆Введите номер поезда🚆:")
    await TrainInfoForm.TRAIN_NUMBER.set()


@dp.message_handler(commands=['cancel'], state=TrainInfoForm.TRAIN_NUMBER)
async def cancel_start_to_save(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Действие было отменено. Вы можете начать снова, используя доступные команды.")


@dp.message_handler(lambda message: message.text.startswith('/'), state=TrainInfoForm.TRAIN_NUMBER)
async def handle_commands_in_start_to_save(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, завершите текущее действие или используйте /cancel для отмены.")


@dp.message_handler(state=TrainInfoForm.TRAIN_NUMBER)
async def input_train_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['train_number'] = message.text
    await message.reply("🕖Введите время отправления (в формате ГГГГ-ММ-ДД ЧЧ:ММ)🕖:")
    await TrainInfoForm.DEPARTURE_TIME.set()


@dp.message_handler(state=TrainInfoForm.DEPARTURE_TIME)
async def input_departure_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['departure_time'] = message.text
    await message.reply("🚉Введите пункт отправления:🚉")
    await TrainInfoForm.DEPARTURE.set()


@dp.message_handler(state=TrainInfoForm.DEPARTURE)
async def input_departure(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['departure'] = message.text
    await message.reply("🚉Введите пункт назначения🚉:")
    await TrainInfoForm.DESTINATION.set()


@dp.message_handler(state=TrainInfoForm.DESTINATION)
async def input_destination(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['destination'] = message.text
        train_number = data['train_number']
        departure_time = data['departure_time']
        departure = data['departure']
        destination = data['destination']

        conn = psycopg2.connect(database="your_database", user="your_usename", password="your+passwaord", host="your_host")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trains (train_number, departure_time, departure, destination) VALUES (%s, %s, %s, %s)",
                       (train_number, departure_time, departure, destination))
        conn.commit()
        conn.close()

        await message.reply(f"🚆Информация о поезде {train_number} сохранена в базе данных.")
        await state.finish()


@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    # Отправьте сообщение пользователю о том, что действие было отменено.
    await message.reply("Действие было отменено. Вы можете начать снова, используя доступные команды.")


@dp.message_handler(commands=['view'])
async def view_data(message: types.Message):
    conn = psycopg2.connect(database="your_database", user="your_usename", password="your+passwaord", host="your_host")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trains")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.reply("В базе данных нет данных о поездах.")
    else:
        response = "Данные о 🚆поездах 🚆в базе данных:\n"
        for row in rows:
            response += f"🚆Номер поезда🚆: {row[1]}\n🕖Время отправления🕖: {row[2]}\n🚉Пункт отправления🚉: {row[3]}\n🚉Пункт назначения🚉: {row[4]}\n\n"
        await message.reply(response)


@dp.message_handler(commands=['delete'])
async def delete_data_start(message: types.Message):
    await message.reply("Введите номер поезда, который вы хотите удалить:")
    await TrainInfoForm.DELETE_CONFIRM.set()


@dp.message_handler(lambda message: not message.text.startswith('/'), state=TrainInfoForm.DELETE_CONFIRM)
async def delete_data_confirm(message: types.Message, state: FSMContext):
    train_number = message.text

    conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trains WHERE train_number = %s", (train_number,))
    conn.commit()
    conn.close()

    await message.reply(f"Данные о поезде с номером {train_number} были успешно удалены из базы данных.")
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
