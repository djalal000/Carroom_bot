import sqlite3
import os

conn = sqlite3.connect('cars.db', check_same_thread=False)
# Enable row factory for better data access
conn.row_factory = sqlite3.Row
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
    """ANY user can add car - with type enforcement"""
    cursor.execute("""
        INSERT INTO cars (user_id, username, model, year, price, miles, location, condition, phone, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id), 
        str(username), 
        str(model), 
        int(year), 
        int(price), 
        int(miles), 
        str(location), 
        int(condition), 
        str(phone), 
        str(image_path) if image_path else None
    ))
    
    car_id = cursor.lastrowid
    conn.commit()
    return car_id

def get_cars_under_price(max_price, limit=30):
    """Get cars under specific price - returns tuples"""
    cursor.execute("""
        SELECT id, user_id, username, model, year, price, miles, location, 
               condition, phone, image_path, created_at
        FROM cars 
        WHERE price <= ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (int(max_price), int(limit)))
    return cursor.fetchall()

def get_car_by_id(car_id):
    """Get single car by ID"""
    cursor.execute("""
        SELECT id, user_id, username, model, year, price, miles, location, 
               condition, phone, image_path, created_at
        FROM cars 
        WHERE id = ?
    """, (int(car_id),))
    return cursor.fetchone()

def get_user_cars(user_id):
    """Get all cars for specific user"""
    cursor.execute("""
        SELECT id, user_id, username, model, year, price, miles, location, 
               condition, phone, image_path, created_at
        FROM cars 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (int(user_id),))
    return cursor.fetchall()

def delete_car(car_id, user_id):
    """Delete car if user owns it"""
    cursor.execute("""
        DELETE FROM cars 
        WHERE id = ? AND user_id = ?
    """, (int(car_id), int(user_id)))
    deleted = cursor.rowcount > 0
    conn.commit()
    return deleted

def get_user_language(user_id):
    """Get user language preference"""
    cursor.execute("SELECT language FROM user_settings WHERE user_id = ?", (int(user_id),))
    result = cursor.fetchone()
    return result[0] if result else 'en'

def set_user_language(user_id, lang):
    """Set user language preference"""
    cursor.execute("""
        INSERT OR REPLACE INTO user_settings (user_id, language)
        VALUES (?, ?)
    """, (int(user_id), str(lang)))
    conn.commit()


init_db()