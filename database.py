import sqlite3
import os

DB_PATH = "cybergram.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT DEFAULT '',
            profile_pic TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image TEXT NOT NULL,
            caption TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Seed hardcoded users (plaintext passwords - intentionally vulnerable)
    hardcoded_users = [
        ("admin", "admin123", "CyberGram administrator", ""),
        ("alice", "password", "Photography enthusiast 📸", ""),
        ("bob", "bob2024", "Just vibing ✌️", ""),
    ]

    for username, password, bio, pic in hardcoded_users:
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password, bio, profile_pic) VALUES (?, ?, ?, ?)",
            (username, password, bio, pic),
        )

    conn.commit()
    conn.close()
