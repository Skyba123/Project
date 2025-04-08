from bot_instance import bot
from telebot import types
from database import conn, cursor
from config import ADMIN_IDS

def register_admin_handlers():
    @bot.message_handler(commands=['admin'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "Ви не маєте прав адміністратора.")
            return
        admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        admin_keyboard.add("/add_item", "/remove_item", "/orders")
        bot.send_message(message.chat.id, "Адмін-режим. Оберіть дію:", reply_markup=admin_keyboard)

    @bot.message_handler(commands=['add_item'])
    def add_item(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "Ви не маєте прав адміністратора.")
            return
        instr = ("Введіть дані нового автомобіля у форматі:\n"
                 "Назва | Опис | Ціна (грн/день)")
        msg = bot.send_message(message.chat.id, instr)
        bot.register_next_step_handler(msg, process_add_item)

    def process_add_item(message):
        try:
            parts = message.text.split("|")
            if len(parts) != 3:
                bot.send_message(message.chat.id, "Невірний формат. Дотримуйтесь інструкції.")
                return
            name = parts[0].strip()
            description = parts[1].strip()
            price = float(parts[2].strip())
            cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
            conn.commit()
            product_id = cursor.lastrowid
            bot.send_message(message.chat.id, f"Автомобіль '{name}' додано до каталогу з ID {product_id}.")
        except ValueError:
            bot.send_message(message.chat.id, "Ціна повинна бути числом. Спробуйте ще раз.")

    @bot.message_handler(commands=['remove_item'])
    def remove_item(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "Ви не маєте прав адміністратора.")
            return
        msg = bot.send_message(message.chat.id, "Введіть ID автомобіля, який потрібно видалити:")
        bot.register_next_step_handler(msg, process_remove_item)

    def process_remove_item(message):
        try:
            product_id = int(message.text.strip())
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            if cursor.rowcount:
                bot.send_message(message.chat.id, f"Автомобіль з ID {product_id} видалено.")
            else:
                bot.send_message(message.chat.id, "Автомобіль з таким ID не знайдено.")
        except ValueError:
            bot.send_message(message.chat.id, "ID повинен бути числом. Спробуйте ще раз.")

    @bot.message_handler(commands=['orders'])
    def list_orders(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "Ви не маєте прав адміністратора.")
            return
        cursor.execute("SELECT id, user_id, username, product_id FROM orders")
        orders = cursor.fetchall()
        if not orders:
            bot.send_message(message.chat.id, "Немає нових замовлень.")
            return

        orders_msg = "Список замовлень:\n"
        for idx, order in enumerate(orders, start=1):
            order_id, user_id, username, product_id = order
            cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
            prod = cursor.fetchone()
            prod_info = f"{prod[0]} за {prod[1]} грн/день" if prod else "Невідомий товар"
            orders_msg += f"{idx}. Користувач: @{username} (ID: {user_id}) замовив: {prod_info}\n"
        bot.send_message(message.chat.id, orders_msg)