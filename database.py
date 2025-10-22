import sqlite3
import os

conn = sqlite3.connect('cars.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    """Initialize database tables"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price INTEGER NOT NULL,
            miles INTEGER NOT NULL,
            location TEXT NOT NULL,
            condition INTEGER NOT NULL,
            phone TEXT NOT NULL,
            image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'en'
        )
    """)
    conn.commit()

def add_car(user_id, username, model, year, price, miles, location, condition, phone, image_path):
    """ANY user can add car - FIXED for SQLite"""
    cursor.execute("""
        INSERT INTO cars (user_id, username, model, year, price, miles, location, condition, phone, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, model, year, price, miles, location, condition, phone, image_path))
    
    car_id = cursor.lastrowid  # ✅ FIXED - works on ALL SQLite versions
    conn.commit()
    return car_id

def get_cars_under_price(max_price, limit=30):
    """Get cars under specific price"""
    cursor.execute("""
        SELECT * FROM cars 
        WHERE price <= ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (max_price, limit))
    return cursor.fetchall()

def get_car_by_id(car_id):
    """Get single car by ID"""
    cursor.execute("SELECT * FROM cars WHERE id = ?", (car_id,))
    return cursor.fetchone()

def get_user_cars(user_id):
    """Get all cars for specific user"""
    cursor.execute("""
        SELECT * FROM cars 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    return cursor.fetchall()

def delete_car(car_id, user_id):
    """Delete car if user owns it"""
    cursor.execute("""
        DELETE FROM cars 
        WHERE id = ? AND user_id = ?
    """, (car_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    return deleted

def get_user_language(user_id):
    """Get user language preference"""
    cursor.execute("SELECT language FROM user_settings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 'en'

def set_user_language(user_id, lang):
    """Set user language preference"""
    cursor.execute("""
        INSERT OR REPLACE INTO user_settings (user_id, language)
        VALUES (?, ?)
    """, (user_id, lang))
    conn.commit()

# Initialize database on import
init_db()