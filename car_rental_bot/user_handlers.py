from bot_instance import bot
from telebot import types
from database import conn, cursor
from config import ADMIN_IDS

def register_user_handlers():
    main_reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_reply_keyboard.add("/start", "/catalog", "/info", "/help")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome_text = (
            "Привіт! Я бот оренди авто.\n"
            "Я допоможу Вам переглядати доступні автомобілі, оформлювати замовлення, "
            "залишати відгуки та надавати іншу інформацію.\n\n"
            "Використовуйте команди:\n"
            "/catalog – перегляд каталогу авто\n"
            "/info – інформація про бота\n"
            "/help – список команд"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_reply_keyboard)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_text = (
            "Список доступних команд:\n"
            "/start - Запуск бота та основне меню\n"
            "/help - Список команд\n"
            "/info - Інформація про бота\n"
            "/catalog - Перегляд каталогу авто\n"
            "/order - Оформлення замовлення (альтернативний спосіб)\n"
            "/feedback - Залишити відгук\n"
            "/admin - Меню адміністратора (тільки для адміністраторів)\n"
            "\nЩоб зробити замовлення: перейдіть до /catalog, оберіть авто та натисніть кнопку 'Замовити'."
        )
        bot.send_message(message.chat.id, help_text, reply_markup=main_reply_keyboard)

    @bot.message_handler(commands=['info'])
    def send_info(message):
        info_text = (
            "Я бот оренди авто. Допомагаю переглядати автомобілі, оформлювати замовлення та залишати відгуки.\n"
            "Також маю адміністративний функціонал для управління каталогом та замовленнями."
        )
        bot.send_message(message.chat.id, info_text, reply_markup=main_reply_keyboard)

    @bot.message_handler(commands=['catalog'])
    def send_catalog(message):
        cursor.execute("SELECT id, name, price FROM products")
        products = cursor.fetchall()
        if not products:
            bot.send_message(message.chat.id, "На даний момент каталог порожній. Очікуйте нових автомобілів.")
            return

        catalog_msg = "Доступні автомобілі для оренди:\n"
        markup = types.InlineKeyboardMarkup()
        for prod in products:
            product_id, name, price = prod
            button_text = f"{name} – {price} грн/день"
            btn = types.InlineKeyboardButton(button_text, callback_data=f"product_{product_id}")
            markup.add(btn)
        bot.send_message(message.chat.id, catalog_msg, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        if call.data.startswith("product_"):
            try:
                product_id = int(call.data.split("_")[1])
                cursor.execute("SELECT id, name, description, price FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                if product:
                    _, name, description, price = product
                    details = (
                        f"Назва: {name}\n"
                        f"Опис: {description}\n"
                        f"Ціна: {price} грн/день"
                    )
                    markup = types.InlineKeyboardMarkup()
                    order_btn = types.InlineKeyboardButton("Замовити", callback_data=f"order_{product_id}")
                    markup.add(order_btn)
                    bot.send_message(call.message.chat.id, details, reply_markup=markup)
                else:
                    bot.send_message(call.message.chat.id, "Товар не знайдено.")
            except Exception as e:
                bot.send_message(call.message.chat.id, "Сталася помилка при обробці даних.")
        elif call.data.startswith("order_"):
            try:
                product_id = int(call.data.split("_")[1])
                cursor.execute(
                    "INSERT INTO orders (user_id, username, product_id) VALUES (?, ?, ?)",
                    (call.from_user.id, call.from_user.username, product_id)
                )
                conn.commit()
                cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                if product:
                    name, price = product
                    order_info = (
                        f"Новий заказ!\n"
                        f"Користувач: @{call.from_user.username} (ID: {call.from_user.id})\n"
                        f"Замовив: {name}\n"
                        f"Ціна: {price} грн/день"
                    )
                    for admin in ADMIN_IDS:
                        try:
                            bot.send_message(admin, order_info)
                        except Exception as e:
                            print(f"Не вдалося надіслати повідомлення адміну: {e}")
                    bot.send_message(call.message.chat.id, f"Ваше замовлення на '{name}' прийняте!")
                else:
                    bot.send_message(call.message.chat.id, "Товар не знайдено.")
            except Exception as e:
                bot.send_message(call.message.chat.id, "Сталася помилка при оформленні замовлення.")

    @bot.message_handler(commands=['order'])
    def order_command(message):
        bot.send_message(message.chat.id, "Для оформлення замовлення перейдіть до каталогу (/catalog) та оберіть автомобіль.")

    @bot.message_handler(commands=['feedback'])
    def feedback_command(message):
        msg = bot.send_message(message.chat.id, "Введіть свій відгук:")
        bot.register_next_step_handler(msg, process_feedback)

    def process_feedback(message):
        cursor.execute(
            "INSERT INTO feedback (user_id, username, feedback) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.text)
        )
        conn.commit()
        admin_msg = (
            f"Новий відгук від @{message.from_user.username} (ID: {message.from_user.id}):\n{message.text}"
        )
        for admin in ADMIN_IDS:
            try:
                bot.send_message(admin, admin_msg)
            except Exception as e:
                print(f"Помилка при відправці відгуку адміну: {e}")
        bot.send_message(message.chat.id, "Дякуємо за Ваш відгук!")
