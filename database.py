import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

DB_PATH = 'prices.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            price REAL,
            sentiment_score REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            processed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_price(date: str, price: float, sentiment_score: float = 0.0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO price_history (date, price, sentiment_score)
        VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            price = excluded.price,
            sentiment_score = excluded.sentiment_score
    ''', (date, price, sentiment_score))
    conn.commit()
    conn.close()

def get_latest_price() -> Optional[Tuple[str, float]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT date, price FROM price_history ORDER BY date DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row

def get_history(days: int = 30) -> List[Tuple[str, float, float]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, price, sentiment_score FROM price_history
        ORDER BY date DESC LIMIT ?
    ''', (days,))
    rows = cursor.fetchall()
    conn.close()
    return rows[::-1]

def update_sentiment_for_today(sentiment: float):
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE price_history SET sentiment_score = ?
        WHERE date = ?
    ''', (sentiment, today))
    if cursor.rowcount == 0:
        # اگر امروز هنوز قیمتی ثبت نشده، یک رکورد بدون قیمت بساز
        cursor.execute('''
            INSERT INTO price_history (date, price, sentiment_score)
            VALUES (?, 0, ?)
        ''', (today, sentiment))
    conn.commit()
    conn.close()

def is_url_processed(url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM news_log WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_url_processed(url: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO news_log (url, processed_at) VALUES (?, ?)',
                   (url, datetime.now().isoformat()))
    conn.commit()
    conn.close()
