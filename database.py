# database.py
import sqlite3
from config import DATABASE_PATH

def connect_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            model TEXT,
            year INTEGER,
            price INTEGER,
            phone TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_car(user_id, username, model, year, price, phone, image_path):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cars (user_id, username, model, year, price, phone, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, model, year, price, phone, image_path))
    conn.commit()
    car_id = c.lastrowid
    conn.close()
    return car_id

def get_cars_under_price(max_price, limit=50, offset=0):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        SELECT id, user_id, username, model, year, price, phone, image_path, created_at
        FROM cars
        WHERE price <= ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (max_price, limit, offset))
    rows = c.fetchall()
    conn.close()
    return rows

def get_car_by_id(car_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cars WHERE id = ?', (car_id,))
    row = c.fetchone()
    conn.close()
    return row
