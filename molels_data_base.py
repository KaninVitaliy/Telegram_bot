import sqlalchemy as sq
from sqlalchemy import func
from sqlalchemy.orm import declarative_base, sessionmaker
import json
import random

Base = declarative_base()

DSN = 'postgresql://postgres:v12mm1997@localhost:5432/bot_telegram'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


class Publisher(Base):
    __tablename__ = 'publisher'

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), unique=True)

    def __str__(self):
        return f'Publisher: {self.id}: , Name: {self.name}'


class Word(Base):
    __tablename__ = 'word'

    id = sq.Column(sq.Integer, primary_key=True)
    russian_word = sq.Column(sq.String(length=40), unique=True)
    target_word = sq.Column(sq.String(length=40), unique=True)


class Publisher_Word(Base):
    __tablename__ = 'Publisher_word'

    id = sq.Column(sq.Integer, primary_key=True)
    id_publisher = sq.Column(sq.Integer, sq.ForeignKey("publisher.id"), nullable=False)
    id_word = sq.Column(sq.Integer, sq.ForeignKey("word.id"), nullable=False)

    def __str__(self):
        return f'Stock: {self.id}: , id_book: {self.id_book}, id_shop: {self.id_shop}, count: {self.count}'


def insert_data(session, name, user_id):
    with open("word.json", "r", encoding="utf-8") as file:
        file = json.load(file)
    count = 0
    for str in file:
        count += 1
        if not session.query(Publisher).filter(Publisher.id == user_id).all():
            id_name_publisher = Publisher(id=user_id, name=name)
            session.add(id_name_publisher)
            session.commit()
        if not session.query(Word).filter(Word.id == count).all():  # Проверка есть ли слово
            new_word = Word(id=count, russian_word=str["russian_word"].lower(), target_word=str["target_word"].lower())
            session.add(new_word)
            session.commit()

        new_id_publisher_word = Publisher_Word(id_publisher=user_id, id_word=count)
        session.add(new_id_publisher_word)
        session.commit()



def delete_word_base(id_user, word):
    word_in_base = sq.select(Word.id) \
        .select_from(Word) \
        .where(Word.target_word == word)
    for word_name in session.execute(word_in_base).all():
        id_word = word_name[0]

    delete_from_Publisher_Word = sq.delete(Publisher_Word).where(Publisher_Word.id == id_word)
    session.execute(delete_from_Publisher_Word)
    session.commit()


def random_word(user_id): # Просто генерировать слово
    id_word = sq.select(Publisher_Word.id_word) \
         .select_from(Publisher_Word) \
         .where(Publisher_Word.id_publisher == user_id)
    id_random_word = random.choice(session.execute(id_word).all())[0]
    word_select = sq.select(Word.russian_word, Word.target_word) \
        .select_from(Word) \
        .where(Word.id == id_random_word)
    word_split = session.execute(word_select).all()[0]
    return word_split

def random_word_examination(user_id, quess_list): # генерировать слова пока не выдадим то слово которого нет в списке
    id_split = []
    for i in quess_list[user_id]:
        id = sq.select(Word.id) \
            .select_from(Word) \
            .where(Word.target_word == i.lower())
        id_word_base = session.execute(id).all()[0][0]
        id_split.append(id_word_base)

    spisok_exam = []
    while len(spisok_exam) < 1:
        id_word = sq.select(Publisher_Word.id_word) \
            .select_from(Publisher_Word) \
            .where(Publisher_Word.id_publisher == user_id)
        id_random_word = random.choice(session.execute(id_word).all())[0]
        if id_random_word not in id_split:
            spisok_exam.append(id_random_word)
        else:
            pass
    word_select = sq.select(Word.russian_word, Word.target_word) \
        .select_from(Word) \
        .where(Word.id == spisok_exam[0])
    word_split = session.execute(word_select).all()[0]
    return word_split


def add_word_base(word_split, user_id):
    russian_word = word_split[1].lower()
    target_word = word_split[0].lower()

    global message_add
    message_add = None
    request_russian = sq.select(Word.id) \
        .select_from(Word) \
        .where(Word.russian_word == russian_word) # Проверка есть ли слово русское
    request_russian = session.execute(request_russian).all()
    request_target = sq.select(Word.id) \
        .select_from(Word) \
        .where(Word.target_word == target_word)
    request_target = session.execute(request_target).all() # Проверка есть ли английское слово
    if request_russian == [] and request_target == []: # Проверка есть ли это слово
        request_base = sq.select(func.max(Word.id)) \
            .select_from(Word) \
            .group_by(Word.id) \
            .order_by(Word.id)
        id_max_word = session.execute(request_base).all()[-1] # Вывели список и самый последний id будет максимальный
        id_word_add = id_max_word[0] + 1
        new_word = Word(id=id_word_add, russian_word=russian_word, target_word=target_word)
        session.add(new_word) # слово добавлено
        session.commit()
        new_id_publisher_word = Publisher_Word(id_publisher=user_id, id_word=id_word_add)
        session.add(new_id_publisher_word)
        session.commit()
        message_add = True
        print("Слово добавлено")

    else:
        message_add = update_word_Publisher(russian_word, target_word, user_id)

    return message_add


def update_word_Publisher(russian_word, target_word, user_id):
    request_base_russian_word = sq.select(Word.id) \
        .select_from(Word) \
        .where(
        russian_word == Word.russian_word)  # Запрос в базу, чтобы вывести id слова
    id_word_russian = session.execute(request_base_russian_word).all()
    request_base_target_word = sq.select(Word.id) \
        .select_from(Word) \
        .where(
        target_word == Word.target_word)  # Запрос в базу, чтобы вывести id слова
    id_word_target = session.execute(request_base_target_word).all()
    if id_word_russian:
        id_word = id_word_russian[-1][0]
    else:
        id_word = id_word_target[-1][0]

    request_base_publisher = sq.select(Publisher_Word.id_publisher) \
        .select_from(Publisher_Word) \
        .where(id_word == Publisher_Word.id_word)
    id_Publisher = session.execute(
        request_base_publisher).all()  # Запрос в базу, чтобы вывести id пользователей у которых есть это слово
    list_id = list(map(lambda x: x[0], id_Publisher))
    if user_id in list_id:
        message_add = False
    else:
        new_id_publisher_word = Publisher_Word(id_publisher=user_id, id_word=id_word)
        session.add(new_id_publisher_word)
        session.commit()
        message_add = True

    return message_add

def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
