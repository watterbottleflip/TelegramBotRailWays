import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token="6079500895:AAGtu2k8sWrPrexqhuUqZz3g6lFLxgWIXLE")
dp = Dispatcher(bot, storage=MemoryStorage())

class TrainInfoForm(StatesGroup):
    TRAIN_NUMBER = State()
    DEPARTURE_TIME = State()
    DEPARTURE = State()
    DESTINATION = State()
    DELETE_CONFIRM = State()
    EDIT_CHOICE = State()
    EDIT_TRAIN_NUMBER = State()
    EDIT_DEPARTURE_TIME = State()
    EDIT_DEPARTURE = State()
    EDIT_DESTINATION = State()


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

        conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
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
    conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
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


@dp.message_handler(commands=['edit'])
async def edit_data_start(message: types.Message):
    await message.reply(f"Выберите что хотите отредактировать: \n1 - Номер поезда🚆\n2 - Время отправления🕖\n3 - Пункт отправления🚉\n4 - 🚉Пункт назначения")
    await TrainInfoForm.EDIT_CHOICE.set()


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) in [1, 2, 3, 4], state=TrainInfoForm.EDIT_CHOICE)
async def edit_data_choose_parameter(message: types.Message, state: FSMContext):
    choice = int(message.text)

    if choice == 1:
        await message.reply("Введите новый номер поезда:")
        await TrainInfoForm.EDIT_TRAIN_NUMBER.set()
    elif choice == 2:
        await message.reply("Введите новое время отправления (в формате ГГГГ-ММ-ДД ЧЧ:ММ):")
        await TrainInfoForm.EDIT_DEPARTURE_TIME.set()
    elif choice == 3:
        await message.reply("Введите новый пункт отправления:")
        await TrainInfoForm.EDIT_DEPARTURE.set()
    elif choice == 4:
        await message.reply("Введите новый пункт назначения:")
        await TrainInfoForm.EDIT_DESTINATION.set()


@dp.message_handler(lambda message: not message.text.startswith('/'), state=TrainInfoForm.EDIT_TRAIN_NUMBER)
async def edit_train_number(message: types.Message, state: FSMContext):
    new_train_number = message.text

    # Move the 'train_number' variable definition inside the function
    train_number = None  # You can initialize it to a default value or retrieve it from state if needed

    async with state.proxy() as data:
        # If you need to retrieve 'train_number' from state, do it here
        if 'current_train' in data:
            train_number = data['current_train'].get('train_number', None)

    # Check if train_number is defined and not None before using it
    if train_number is not None:
        conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
        cursor = conn.cursor()
        cursor.execute("UPDATE trains SET train_number = %s WHERE train_number = %s", (new_train_number, train_number))
        conn.commit()
        conn.close()

        await message.reply(f"Обновленный номер поезда: {new_train_number}")
    else:
        await message.reply("Ошибка: Номер поезда не определен")

    await state.finish()
    await message.reply("Редактирование завершено.")



@dp.message_handler(lambda message: not message.text.startswith('/'), state=TrainInfoForm.EDIT_DEPARTURE_TIME)
async def edit_departure_time(message: types.Message, state: FSMContext):
    new_departure_time = message.text
    async with state.proxy() as data:
        train_number = data['current_train']['train_number']

    conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("UPDATE trains SET departure_time = %s WHERE train_number = %s", (new_departure_time, train_number))
    conn.commit()
    conn.close()

    await message.reply(f"Обновленное время отправления: {new_departure_time}")
    await state.finish()
    await message.reply("Редактирование завершено.")


@dp.message_handler(lambda message: not message.text.startswith('/'), state=TrainInfoForm.EDIT_DEPARTURE)
async def edit_departure(message: types.Message, state: FSMContext):
    new_departure = message.text
    async with state.proxy() as data:
        train_number = data['current_train']['train_number']

    conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("UPDATE trains SET departure = %s WHERE train_number = %s", (new_departure, train_number))
    conn.commit()
    conn.close()

    await message.reply(f"Обновленный пункт отправления: {new_departure}")
    await state.finish()
    await message.reply("Редактирование завершено.")


@dp.message_handler(lambda message: not message.text.startswith('/'), state=TrainInfoForm.EDIT_DESTINATION)
async def edit_destination(message: types.Message, state: FSMContext):
    new_destination = message.text
    async with state.proxy() as data:
        train_number = data['current_train']['train_number']

    conn = psycopg2.connect(database="RailWays", user="postgres", password="Admin1234", host="localhost")
    cursor = conn.cursor()
    cursor.execute("UPDATE trains SET destination = %s WHERE train_number = %s", (new_destination, train_number))
    conn.commit()
    conn.close()

    await message.reply(f"Обновленный пункт назначения: {new_destination}")
    await state.finish()
    await message.reply("Редактирование завершено.")


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
