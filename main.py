import random
import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from molels_data_base import Publisher, create_tables, Word, Publisher_Word, insert_data, random_word, delete_word_base, \
    add_word_base, random_word_examination

with open("settings.json", "r") as file:
    settings_program = json.load(file)

DNS = settings_program["DNS"]
engine = sqlalchemy.create_engine(DNS)
Session = sessionmaker(bind=engine)
session = Session()

state_storage = StateMemoryStorage()
token = settings_program["token_telegram"]
bot = TeleBot(token, state_storage=state_storage)

known_users = []
global quess_list
quess_list = {}
userStep = {}
buttons = []


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


def show_hint(*lines):
    return '\n'.join(lines)


@bot.message_handler(commands=["cards", "start"])
def start_bot(message):
    cid = message.chat.id
    name = message.from_user.first_name
    user_id = message.from_user.id

    save_data(session, name, user_id)

    print(name)
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, f"Привет, {name}, время изучить несколько новых английских слов!")

    global buttons
    buttons = []
    markup = types.ReplyKeyboardMarkup(row_width=2)
    count_word = random_word(user_id)
    russian_word = count_word[0].title()
    target_word = count_word[1].title()
    target_word_btn = types.KeyboardButton(target_word)
    others_words = []
    quess_list[user_id] = []
    while len(others_words) < 4:
        word = random_word(user_id)[1].title()
        if word not in others_words and word != target_word:
            others_words.append(word)
        else:
            pass
    other_words_button = [types.KeyboardButton(word) for word in others_words]

    buttons = [target_word_btn] + other_words_button
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)
    bot.send_message(message.chat.id, f"Угадай слово {russian_word}", reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = russian_word
        data['other_words'] = others_words


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    global buttons
    buttons = []
    markup = types.ReplyKeyboardMarkup(row_width=2)
    count_word = random_word_examination(message.from_user.id, quess_list)
    russian_word = count_word[0].title()
    target_word = count_word[1].title()
    target_word_btn = types.KeyboardButton(target_word)
    others_words = []
    while len(others_words) < 4:
        word = random_word(message.from_user.id)[1].title()
        if word not in others_words and word != target_word:
            others_words.append(word)
        else:
            pass
    other_words_button = [types.KeyboardButton(word) for word in others_words]

    buttons = [target_word_btn] + other_words_button
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)
    bot.send_message(message.chat.id, f"Угадай слово {russian_word}", reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = russian_word
        data['other_words'] = others_words


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        delete_word_base(message.from_user.id, data['target_word'].lower()) # Удаляем слово для конкретного пользователя
        del_word = show_target(data)
        del_word_text = ["Удалено!✔️", del_word]
        del_word = show_hint(*del_word_text)
    markup.add(*buttons)
    bot.send_message(message.chat.id, del_word, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def update_word_1(message):
    text_mesage_1 = bot.send_message(message.from_user.id, 'Введите слово на английском: ')
    bot.register_next_step_handler(text_mesage_1, after_text_1)


def after_text_1(message):
    global word_add
    word_add = []
    word_english = message.text
    if word_english not in [i.text for i in buttons]: # Проверка есть ли это слово в кнопках
        word_add.append(word_english)
        text_mesage_2 = bot.send_message(message.from_user.id, 'Введите слово на русском: ')
        bot.register_next_step_handler(text_mesage_2, after_text_2)
    else:
        print("Запрещено!")
        text_mesage_2 = bot.send_message(message.from_user.id, 'Запрещено! Введите слово на Английском: ')
        bot.register_next_step_handler(text_mesage_2, after_text_1)


def after_text_2(message):
    word_russian = message.text
    word_add.append(word_russian)
    if add_word_base(word_add, message.from_user.id):
        text_message = "Слово добавлено 👌"
        bot.send_message(message.from_user.id, text_message)
    else:
        text_message = "Слово уже есть , попробуйте еще"
        bot.send_message(message.from_user.id, text_message)
        text_mesage_2 = bot.send_message(message.from_user.id, 'Введите слово на Английском: ')
        bot.register_next_step_handler(text_mesage_2, after_text_1)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = [hint, "Отлично!❤. Давай дальше!"]
            hint = show_hint(*hint_text)
            quess_list[message.from_user.id].append(text)
            print(quess_list)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


def save_data(session, name, user_id):
    insert_data(session, name, user_id)


if __name__ == '__main__':
    print("Start Telegram bot...")
    # создадим базу данных, авторизуем пользователя и загрузим слова для угадывания
    create_tables(engine)
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.polling(none_stop=True)
