import sqlite3
import hashlib
import os
from config import DB_PATH

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Register new user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        hashed_pwd = hash_password(password)
        c.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, hashed_pwd)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, "Username already exists!"
        elif 'email' in str(e):
            return False, "Email already registered!"
        else:
            return False, "Registration failed!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_user(username, password):
    """Login user by username"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        hashed_pwd = hash_password(password)
        c.execute(
            'SELECT username, email FROM users WHERE username = ? AND password = ?',
            (username, hashed_pwd)
        )
        user = c.fetchone()
        conn.close()
        
        if user:
            return True, user[0]
        else:
            return False, "Invalid username or password!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_email(email):
    """Validate email format"""
    return '@' in email and '.' in email

def user_exists(email):
    """Check if email exists"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def username_exists(username):
    """Check if username exists"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False
