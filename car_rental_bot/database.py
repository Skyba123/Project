import sqlite3
from config import DB_NAME


conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

def initialize_db():
    # Створення таблиці для автомобілів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    conn.commit()

    # Створення таблиці для замовлень
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            product_id INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()

    # Створення таблиці для відгуків
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            feedback TEXT
        )
    ''')
    conn.commit()

    # Заповнення таблиці автомобілів
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_products = [
            ("Toyota Camry", "Комфортний седан для ділових поїздок", 1200),
            ("BMW 3 Series", "Стильний автомобіль для активних водіїв", 1800),
            ("Audi A4", "Елегантний та потужний автомобіль", 1700)
        ]
        cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
        conn.commit()