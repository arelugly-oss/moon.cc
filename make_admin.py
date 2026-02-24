
"""
Phook+ - Make Admin Script (SQLite)
Выдаёт права администратора пользователю
"""

import sqlite3
import os

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASEDIR, 'database.db')

print(f'📁 Путь к базе данных: {DATABASE}')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        email_verified INTEGER DEFAULT 0,
        uid INTEGER,
        joined TEXT,
        is_admin INTEGER DEFAULT 0,
        avatar TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        ip TEXT DEFAULT '',
        last_ip TEXT DEFAULT '',
        last_login TEXT DEFAULT '',
        hwid TEXT DEFAULT '',
        last_spin TEXT DEFAULT ''
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cheat_id INTEGER,
        cheat_name TEXT,
        game TEXT,
        expires TEXT,
        activated TEXT,
        source TEXT DEFAULT '',
        given_by TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cheats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game TEXT,
        name TEXT,
        icon TEXT DEFAULT '',
        icon_type TEXT DEFAULT 'text',
        price REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_code TEXT UNIQUE,
        cheat_id INTEGER,
        days INTEGER,
        created TEXT,
        created_by TEXT,
        used INTEGER DEFAULT 0,
        used_by TEXT DEFAULT '',
        used_at TEXT DEFAULT ''
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        subject TEXT,
        category TEXT,
        message TEXT,
        status TEXT DEFAULT 'open',
        created TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ticket_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        username TEXT,
        message TEXT,
        date TEXT,
        is_admin INTEGER DEFAULT 0,
        FOREIGN KEY (ticket_id) REFERENCES tickets(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        filename TEXT,
        original_name TEXT,
        author TEXT,
        uploaded TEXT,
        downloads INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS resellers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        flag TEXT DEFAULT '',
        link TEXT DEFAULT '#',
        online INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_type TEXT,
        date TEXT,
        count INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS changelog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT,
        date TEXT,
        changes TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ticket_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )''')
    
    default_settings = {
        'discord_link': 'https://discord.gg/phookplus',
        'telegram_link': 'https://t.me/phookplus',
        'youtube_link': '',
        'twitter_link': '',
        'website_name': 'Phook+',
        'loader_version': '1.0.0',
        'loader_filename': '',
        'next_uid': '1',
        'downloads': '0',
        'keys_activated': '0'
    }
    
    for key, value in default_settings.items():
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()
    print('✅ База данных инициализирована!')

def make_admin(username):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    
    if not user:
        print(f'❌ Пользователь "{username}" не найден!')
        conn.close()
        return False
    
    if user['is_admin']:
        print(f'ℹ️ Пользователь "{username}" уже является администратором')
        conn.close()
        return True
    
    c.execute('UPDATE users SET is_admin = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    
    print(f'✅ Пользователь "{username}" теперь администратор!')
    return True

def list_users():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT username, is_admin FROM users')
    users = c.fetchall()
    conn.close()
    
    if not users:
        print('\n📋 Пользователей пока нет. Зарегистрируйтесь на сайте!\n')
        return
    
    print('\n📋 Список пользователей:')
    print('-' * 40)
    for user in users:
        admin_badge = '👑 ADMIN' if user['is_admin'] else ''
        print(f"  {user['username']} {admin_badge}")
    print('-' * 40)
    print(f'Всего: {len(users)} пользователей\n')

def remove_admin(username):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    
    if not user:
        print(f'❌ Пользователь "{username}" не найден!')
        conn.close()
        return False
    
    c.execute('UPDATE users SET is_admin = 0 WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    
    print(f'✅ Права администратора сняты с "{username}"')
    return True

if __name__ == '__main__':
    print('\n🔧 Phook+ Admin Manager (SQLite)\n')
    
    if os.path.exists(DATABASE):
        print(f'✅ Файл БД найден: {DATABASE}')
    else:
        print(f'⚠️ Файл БД не найден, будет создан: {DATABASE}')
    
    init_db()
    
    while True:
        print('\nВыберите действие:')
        print('1. Выдать админку')
        print('2. Снять админку')
        print('3. Список пользователей')
        print('4. Выход')
        
        choice = input('\nВаш выбор (1-4): ').strip()
        
        if choice == '1':
            username = input('Введите имя пользователя: ').strip()
            if username:
                make_admin(username)
        elif choice == '2':
            username = input('Введите имя пользователя: ').strip()
            if username:
                remove_admin(username)
        elif choice == '3':
            list_users()
        elif choice == '4':
            print('👋 До свидания!')
            break
        else:
            print('❌ Неверный выбор')
