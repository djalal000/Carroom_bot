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
            miles INTEGER DEFAULT 0,
            location TEXT DEFAULT '',
            condition INTEGER DEFAULT 0,
            phone TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'en'
        )
    ''')
    conn.commit()
    conn.close()

def add_car(user_id, username, model, year, price, miles, location, condition, phone, image_path):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cars (user_id, username, model, year, price, miles, location, condition, phone, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, model, year, price, miles, location, condition, phone, image_path))
    conn.commit()
    car_id = c.lastrowid
    conn.close()
    return car_id

def get_cars_under_price(max_price, limit=50, offset=0):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        SELECT id, user_id, username, model, year, price, miles, location, condition, phone, image_path, created_at
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

def get_user_cars(user_id, limit=50):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        SELECT id, user_id, username, model, year, price, miles, location, condition, phone, image_path, created_at
        FROM cars
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_car(car_id, user_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        DELETE FROM cars 
        WHERE id = ? AND user_id = ?
    ''', (car_id, user_id))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_user_language(user_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 'en'

def set_user_language(user_id, language):
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, language) 
        VALUES (?, ?)
    ''', (user_id, language))
    conn.commit()
    conn.close()

def migrate_db():
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE cars ADD COLUMN miles INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE cars ADD COLUMN location TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE cars ADD COLUMN condition INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

# Run migration
try:
    migrate_db()
except:
    pass