import telebot
from telebot import types
import psycopg2
from enum import Enum
import random

class Command(Enum):
    NEXT = "Следующее слово"
    DELETE_WORD = "Удалить слово"
    ADD_WORD = "Добавить слово"

user_data = {}

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname='Ntl_Dz_Db_EnRu',
            user='admin',
            password='*******',
            host='95.163.223.80',
            port='5432'
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")

TOKEN = '***********'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
                           (user_id, username))
            conn.commit()
            bot.send_message(message.chat.id, "Добро пожаловать! Используйте команду /cards для начала обучения.")

        @bot.message_handler(commands=['cards'])
        def cards_command(message):
            create_cards(message)

        def create_cards(message):
            user_id = message.from_user.id

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT word, translation FROM words ORDER BY RANDOM() LIMIT 1")
                    word_data = cursor.fetchone()

                    if word_data:
                        word, translation = word_data

                        cursor.execute(
                            "SELECT translation FROM words WHERE translation != %s ORDER BY RANDOM() LIMIT 4",
                            (translation,))
                        wrong_translations = [row[0] for row in cursor.fetchall()]

                        if len(wrong_translations) < 4:
                            additional_needed = 4 - len(wrong_translations)
                            cursor.execute(
                                "SELECT translation FROM words WHERE translation != %s AND translation NOT IN %s ORDER BY RANDOM() LIMIT %s",
                                (translation, tuple(wrong_translations), additional_needed))
                            wrong_translations.extend([row[0] for row in cursor.fetchall()])

                        if len(wrong_translations) > 4:
                            wrong_translations = random.sample(wrong_translations, 4)

                        options = wrong_translations + [translation]
                        random.shuffle(options)

                        markup = types.ReplyKeyboardMarkup(row_width=2)

                        user_data[user_id] = {'target_word': word, 'translate_word': translation}

                        for option in options:
                            markup.add(types.KeyboardButton(option))

                        markup.add(types.KeyboardButton(Command.NEXT.value),
                                   types.KeyboardButton(Command.DELETE_WORD.value),
                                   types.KeyboardButton(Command.ADD_WORD.value))

                        bot.send_message(message.chat.id, f"Как переводится слово: {word}?", reply_markup=markup)

        @bot.message_handler(func=lambda message: message.text == Command.NEXT.value)
        def next_cards(message):
            create_cards(message)

        @bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD.value)
        def delete_word(message):
            user_id = message.from_user.id

            if user_id not in user_data:
                bot.send_message(message.chat.id, "Сначала выберите слово с помощью команды /cards.")
                return

            word_to_delete = user_data[user_id]['target_word']

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM words WHERE word = %s", (word_to_delete,))
                    conn.commit()

            bot.send_message(message.chat.id, f"Слово '{word_to_delete}' удалено.")

        @bot.message_handler(func=lambda message: message.text == Command.ADD_WORD.value)
        def add_word(message):
            bot.send_message(message.chat.id,
                             "Пожалуйста, введите слово и его перевод через пробел (например: 'слово перевод').")
            bot.register_next_step_handler(message, process_new_word)

        def process_new_word(message):
            try:
                word, translation = message.text.split(' ', 1)
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO words (word, translation) VALUES (%s, %s)",
                                       (word, translation))
                        conn.commit()
                bot.send_message(message.chat.id, f"Слово '{word}' с переводом '{translation}' добавлено.")
            except ValueError:
                bot.send_message(message.chat.id, "Ошибка: Пожалуйста, введите слово и перевод корректно.")
            except Exception as e:
                bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

        @bot.message_handler(
            func=lambda message: message.text in user_data.get(message.from_user.id, {}).get('translate_word', []))
        def correct_answer(message):
            bot.send_message(message.chat.id, "Правильно! Поздравляю!")
            next_cards(message)

        @bot.message_handler(
            func=lambda message: message.text not in user_data.get(message.from_user.id, {}).get('translate_word', []))
        def wrong_answer(message):
            bot.send_message(message.chat.id, "Неправильно. Попробуйте снова.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
