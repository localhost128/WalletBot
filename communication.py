from re import match
from datetime import date as dt
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from db_work import DBWork
from ceker import money_chek, date_check


class FSMTransaction(StatesGroup):
    id = State()
    sum = State()
    category = State()
    date = State()
    description = State()
    adding = State()


class FSMEditing(StatesGroup):
    data = State()
    field = State()
    editing = State()


class Communication:

    def __init__(self, token):
        storage = MemoryStorage()
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=storage)

    @staticmethod
    def transform_date(date):
        date = date.split('.')
        return f'{date[2]}-{date[1]}-{date[0]}'

    @staticmethod
    def create_rkm(*args):
        if not all(isinstance(x, str) for x in args):
            raise TypeError
        markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for i in args:
            markup.insert(types.KeyboardButton(i))
        return markup

    @staticmethod
    def create_ikm(*args):
        if not all(isinstance(x, str) for x in args):
            raise TypeError
        markup = types.InlineKeyboardMarkup(resize_keyboard=True)
        for i in args:
            a = i.split(' ')
            markup.insert(types.InlineKeyboardButton(a[0], callback_data=a[1]))
        return markup

    def main(self):
        self.dp.register_message_handler(self.start_help, commands=['start', 'help'])
        self.dp.register_message_handler(self.transaction_help, commands=['transaction_help'])
        self.dp.register_message_handler(self.statistics_help, commands=['statistics_help'])
        self.dp.register_message_handler(self.edit_help, commands=['edit_help'])
        self.dp.register_message_handler(self.add, commands=['add_transaction'], state=None)
        self.dp.register_message_handler(self.statistics, commands=['statistics'])
        self.dp.register_callback_query_handler(self.delete, lambda call: match(r'delete_', call.data))
        self.dp.register_callback_query_handler(self.edit, lambda call: match(r'edit_', call.data))
        self.dp.register_callback_query_handler(self.select_field, lambda call: match(r'field_', call.data))
        self.dp.register_message_handler(self.cancel, state="*", commands=['cancel'])
        self.dp.register_message_handler(self.field_enter, content_types=['text'], state=FSMEditing.field)
        self.dp.register_message_handler(self.editing, state=FSMEditing.editing, commands=['edit'])
        self.dp.register_message_handler(self.sum, content_types=['text'], state=FSMTransaction.sum)
        self.dp.register_message_handler(self.category, content_types=['text'], state=FSMTransaction.category)
        self.dp.register_message_handler(self.date, content_types=['text'], state=FSMTransaction.date)
        self.dp.register_message_handler(self.description, content_types=['text'], state=FSMTransaction.description)
        self.dp.register_message_handler(self.adding, state=FSMTransaction.adding, commands=['ok'])
        self.dp.register_message_handler(self.editing, state="*", commands=['edit'])
        self.dp.register_message_handler(self.order_by_date, commands=['order_by_date'])
        self.dp.register_message_handler(self.order_by_category, commands=['order_by_category'])

        executor.start_polling(self.dp, skip_updates=True)

    async def start_help(self, message: types.Message):
        await message.answer('Hey\n'
                             'I\'m WalletBot\n'
                             'I\'m going to help you with your finances\n\n'
                             'Click /add_transaction to add a transaction\n'
                             'Click /statistics to view statistics\n\n'
                             'If you need help with transactions click /transaction_help\n'
                             'If you need help with statistics click /statistics_help',

                             reply_markup=self.create_rkm('/add_transaction', '/statistics',
                                                          '/transaction_help', '/statistics_help'))

    async def transaction_help(self, message: types.Message):
        await message.answer('To add a new transaction click /add_transaction\n'
                             'Follow the instructions on the screen\n\n'
                             'To enter the amount of income use +0 or 0\n'
                             'To enter the expense amount use -0\n'
                             '(Instead of 0, you can use any format for entering the sum (12, 12.2, 12.34, 12.34))\n\n'
                             'To select a category, you can choose one of the existing ones or create a new one\n\n'
                             'To enter a date use the format dd.mm.yyyy\n'
                             'Or select the option today for today\'s date\n\n'
                             'For description, just enter any text\n\n'
                             'In the end enter /ok\n'
                             'To cancel click /cancel\n\n'
                             'Іf you need help click /help',

                             reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))

    async def statistics_help(self, message: types.Message):
        await message.answer('To view statistics click /add_transaction\n'
                             'To view transactions sorted by date, click /order_by_date\n'
                             'To view transactions sorted by category, click /order_by_category\n\n'
                             'To delete a transaction, click the delete button\n'
                             'Under the message with the desired transaction\n\n'
                             'To edit information about a transaction, click the edit button\n'
                             'Under the message with the required transaction\n\n'
                             'If you need help with edit click /edit_help\n'
                             'Іf you need help click /help',

                             reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help', '/edit_help'))

    async def edit_help(self, message: types.Message):
        await message.answer('To change information about a transaction, click the edit button\n'
                             'Under the message with the required transaction\n\n'
                             'To select the field by which the change will occur, click the edit button\n'
                             'Under the message with the required field\n\n'
                             'Enter the information you want to replace and click /edit\n'
                             'To cancel click /cancel\n\n'
                             'Іf you need help click /help',

                             reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))

    async def add(self, message: types.Message):
        await FSMTransaction.sum.set()
        await message.answer('Enter sum of money(+ for Income , - for Expenses)',
                             reply_markup=self.create_rkm('/cancel'))

    async def sum(self, message: types.Message, state):
        db = DBWork(f'{message.from_user.id}')
        items = list(map(lambda x: list(x)[0], db.select_distinct('category')))
        markup = self.create_rkm('/cancel')
        for i in items:
            markup.add(types.KeyboardButton(i))
        try:
            money_chek(message.text)
            async with state.proxy() as data:
                data['sum'] = message.text
            await message.answer('Enter category', reply_markup=markup)
            await FSMTransaction.next()
        except TypeError as er:
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)

    async def category(self, message: types.Message, state):
        markup = self.create_rkm('/cancel')
        try:
            markup.add(types.KeyboardButton('today'))
            async with state.proxy() as data:
                data['category'] = message.text
            await message.answer('Enter date', reply_markup=markup)
            await FSMTransaction.next()
        except TypeError as er:
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)

    async def date(self, message: types.Message, state):
        markup = self.create_rkm('/cancel')
        try:
            if message.text == 'today':
                now = dt.today()
                message.text = f'{now.day}.{now.month}.{now.year}'
            else:
                date_check(message.text)

            async with state.proxy() as data:
                data['date'] = message.text
            await message.answer('Enter description', reply_markup=markup)
            await FSMTransaction.next()
        except TypeError as er:
            markup.add(types.KeyboardButton('today'))
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)
        except ValueError as er:
            markup.add(types.KeyboardButton('today'))
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)

    async def description(self, message: types.Message, state):

        try:
            async with state.proxy() as data:
                data['description'] = message.text
            async with state.proxy() as data:
                await message.answer(f'{data["sum"]}\n{data["category"]}\n{data["date"]}\n{data["description"]}',
                                     reply_markup=self.create_rkm('/cancel', '/ok'))
            await FSMTransaction.next()
        except TypeError as er:
            await message.answer(f'Wrong entering\n{er}', reply_markup=self.create_rkm('/cancel'))

    async def adding(self, message: types.Message, state):
        async with state.proxy() as data:
            db = DBWork(f'{message.from_user.id}')

            db.insert(data["sum"], data["category"], self.transform_date(data["date"]), data["description"])
            res = db.select_where_max('transact_id', 'transact_id')[0]
            text = f'{"income" if res[1] > 0 else "expense"}\n{abs(res[1])}\ncategory: {res[2]}\n{res[3]}\n{res[4]}'
            await message.answer(f'{text}\nAdded',
                                 reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))
        await state.finish()

    async def cancel(self, message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            await message.answer('Ok', reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))
            return
        await state.finish()
        await message.answer('Ok', reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))

    async def delete(self, call: types.CallbackQuery):
        call_data = call.data.split("_")
        db = DBWork(call_data[2])
        db.delete(call_data[1])
        await call.message.answer('Ready', reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))
        await call.answer()

    async def edit(self, call: types.CallbackQuery):
        call_data = call.data.split("_")
        db = DBWork(f'{call_data[2]}')
        transaction = db.select_where('transact_id', f'{call_data[1]}')[0]
        await call.message.answer(f'{"income" if transaction[1] > 0 else "expense"}\n{abs(transaction[1])}',
                                  reply_markup=self.create_ikm(
                                      f'edit field_sum_{call_data[2]}_{transaction[0]}_{call_data[2]}'))
        await call.message.answer(f'category: {transaction[2]}',
                                  reply_markup=self.create_ikm(
                                      f'edit field_category_{call_data[2]}_{transaction[0]}_{call_data[2]}'))
        await call.message.answer(f'{transaction[3]}',
                                  reply_markup=self.create_ikm(
                                      f'edit field_date_{call_data[2]}_{transaction[0]}_{call_data[2]}'))
        await call.message.answer(f'{transaction[4]}',
                                  reply_markup=self.create_ikm(
                                      f'edit field_description_{call_data[2]}_{transaction[0]}_{call_data[2]}'))
        await call.message.answer('That\'s all',
                                  reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))
        await call.answer()

    async def select_field(self, call: types.CallbackQuery, state):
        call_data = call.data.split('_')
        await FSMEditing.first()

        markup = self.create_rkm('/cancel')

        async with state.proxy() as data:
            data['field'] = call_data[1]
            data['transaction_id'] = call_data[3]
            await FSMEditing.next()
        if call_data[1] == 'category':
            db = DBWork(f'{call_data[4]}')
            items = list(map(lambda x: list(x)[0], db.select_distinct('category')))
            for i in items:
                markup.add(types.KeyboardButton(i))
        elif call_data[1] == 'date':
            markup.add(types.KeyboardButton('today'))

        if call_data[1] == 'sum':
            await call.message.answer('Enter sum of money(+ for Income , - for Expenses)', reply_markup=markup)
        else:
            await call.message.answer(f'Enter {call_data[1]}', reply_markup=markup)
        await call.answer()

    async def field_enter(self, message: types.Message, state):
        markup = self.create_rkm('/cancel')
        try:
            async with state.proxy() as data:
                if data['field'] == 'sum':
                    money_chek(message.text)
                elif data['field'] == 'date':
                    if message.text == 'today':
                        now = dt.today()
                        message.text = f'{now.day}.{now.month}.{now.year}'
                    else:
                        date_check(message.text)
                    message.text = self.transform_date(message.text)
                data['value'] = message.text
                await message.answer(f'{data["field"]}: {data["value"]}',
                                     reply_markup=self.create_rkm('/cancel', '/edit'))
            await FSMTransaction.next()
        except TypeError as er:
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)
        except ValueError as er:
            await message.answer(f'Wrong entering\n{er}', reply_markup=markup)

    async def editing(self, message: types.Message, state):
        db = DBWork(f'{message.from_user.id}')
        async with state.proxy() as data:
            db.update(data['field'], f"\'{data['value']}\'", data['transaction_id'])
            transaction = db.select_where('transact_id', data['transaction_id'])[0]
        await state.finish()
        text = f'{"income" if transaction[1] > 0 else "expense"}\n{abs(transaction[1])}\ncategory: ' \
               f'{transaction[2]}\n{transaction[3]}\n{transaction[4]}\nEdited'
        await message.answer(text, reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))

    async def statistics(self, message: types.Message):
        markup = self.create_rkm('/add_transaction', '/statistics', '/help')
        markup.add(types.KeyboardButton('/order_by_date'))
        markup.insert(types.KeyboardButton('/order_by_category'))
        await message.answer('Select option', reply_markup=markup)

    async def order_by_date(self, message: types.Message):
        db = DBWork(f'{message.from_user.id}')
        for i in db.select_order_by('date'):
            text = f'{"income" if i[1] > 0 else "expense"}\n{abs(i[1])}\ncategory: {i[2]}\n{i[3]}\n{i[4]}'
            await message.answer(text, reply_markup=self.create_ikm(f'edit edit_{i[0]}_{message.from_user.id}',
                                                                    f'delete delete_{i[0]}_{message.from_user.id}'))
        await message.answer('That\'s all', reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))

    async def order_by_category(self, message: types.Message):
        db = DBWork(f'{message.from_user.id}')
        for i in db.select_order_by('category'):
            text = f'{"income" if i[1] > 0 else "expense"}\n{abs(i[1])}\ncategory: {i[2]}\n{i[3]}\n{i[4]}'
            await message.answer(text, reply_markup=self.create_ikm(f'edit edit_{i[0]}_{message.from_user.id}',
                                                                    f'delete delete_{i[0]}_{message.from_user.id}'))

        await message.answer('That\'s all', reply_markup=self.create_rkm('/add_transaction', '/statistics', '/help'))
