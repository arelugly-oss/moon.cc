from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from functools import wraps
from werkzeug.utils import secure_filename
import os
import sqlite3
import json
from datetime import datetime, timedelta
import random
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'qwertyuiopasdfghjklzxcvbnm1234567890@'

SMTP_EMAIL = 'admin@phook.xyz'  # ТУТ БЛЯТЬ ИЗМЕНИ НА СВОЮ ПОЧТУ, НЕ ЗАБУДЬ
SMTP_PASSWORD = 'H%AVW9n9ImVL'   # А ТУТ НА СМТП ПАСВОРД!
SMTP_SERVER = 'smtp.beget.com'
SMTP_PORT = 2525

ALLOWED_EMAIL_DOMAINS = ['gmail.com', 'mail.com', 'ya.ru', 'yandex.ru']

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASEDIR, 'database.db')
UPLOAD_FOLDER = os.path.join(BASEDIR, 'static/uploads')
LOADER_FOLDER = os.path.join(BASEDIR, 'static/loader')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
LOADER_EXTENSIONS = {'exe', 'zip', 'rar'}
DLL_EXTENSIONS = {'dll'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOADER_FOLDER, exist_ok=True)

DLL_FOLDER = os.path.join(BASEDIR, 'static/dlls')
os.makedirs(DLL_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LOADER_FOLDER'] = LOADER_FOLDER
app.config['DLL_FOLDER'] = DLL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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
        last_spin TEXT DEFAULT '',
        coins INTEGER DEFAULT 0,
        last_daily TEXT DEFAULT '',
        login_streak INTEGER DEFAULT 0
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
        active INTEGER DEFAULT 1,
        cheat_type TEXT DEFAULT 'crack',
        main_dll TEXT DEFAULT '',
        main_dll_process TEXT DEFAULT '',
        main_dll_method TEXT DEFAULT 'LoadLibrary',
        extra_dll TEXT DEFAULT '',
        extra_dll_process TEXT DEFAULT '',
        extra_dll_method TEXT DEFAULT 'LoadLibrary',
        api_token TEXT DEFAULT ''
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

    c.execute('''CREATE TABLE IF NOT EXISTS invite_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        created TEXT,
        created_by TEXT,
        max_uses INTEGER DEFAULT 1,
        uses INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_type TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    default_settings = {
        'discord_link': 'https://discord.gg/phookplus',
        'telegram_link': 'https://t.me/phookplus',
        'youtube_link': '',
        'twitter_link': '',
        'roulette_enabled': '1',
        'invite_required': '0',
        'coin_rate': '98',
        'daily_coins': '10',
        'website_name': 'Moon.cc',
        'loader_version': '1.0.0',
        'loader_filename': '',
        'next_uid': '1',
        'downloads': '0',
        'keys_activated': '0'
    }
    
    for key, value in default_settings.items():
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    try:
        c.execute('ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0')
    except:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN last_daily TEXT DEFAULT ""')
    except:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN login_streak INTEGER DEFAULT 0')
    except:
        pass
    
    conn.commit()
    conn.close()

def get_setting(key, default=''):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else default

def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_subscriptions(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
    subs = [dict(row) for row in c.fetchall()]
    conn.close()
    return subs

def get_all_cheats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats')
    cheats = [dict(row) for row in c.fetchall()]
    conn.close()
    return cheats

def get_all_resellers():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM resellers')
    resellers = [dict(row) for row in c.fetchall()]
    conn.close()
    return resellers

def get_all_categories():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM ticket_categories')
    cats = [row['name'] for row in c.fetchall()]
    conn.close()
    return cats

def track_stat(stat_type):
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, count FROM stats WHERE stat_type = ? AND date = ?', (stat_type, today))
    row = c.fetchone()
    if row:
        c.execute('UPDATE stats SET count = count + 1 WHERE id = ?', (row['id'],))
    else:
        c.execute('INSERT INTO stats (stat_type, date, count) VALUES (?, ?, 1)', (stat_type, today))
    conn.commit()
    conn.close()

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


init_db()



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        user = get_user_by_username(session['user'])
        if not user or not user.get('is_admin'):
            flash('Access denied', 'error')
            return redirect(url_for('subscriptions'))
        return f(*args, **kwargs)
    return decorated_function

def has_active_subscription(user_id):
    subs = get_user_subscriptions(user_id)
    now = datetime.now()
    for sub in subs:
        if sub.get('expires'):
            try:
                exp = datetime.strptime(sub['expires'], '%Y-%m-%d %H:%M')
                if exp > now:
                    return True
            except:
                pass
    return False

def send_verification_email(to_email, code):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = 'Moon.cc - Verification Code'
        body = f'''
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0d0d0f; color: #ffffff; padding: 40px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #141418; border-radius: 12px; padding: 40px;">
                <h1 style="text-align: center; margin-bottom: 30px;">Moon.cc</h1>
                <p style="color: #8a8a8f; text-align: center;">Your verification code:</p>
                <div style="background-color: #1a1a1f; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px;">{code}</span>
                </div>
                <p style="color: #5a5a5f; text-align: center; font-size: 12px;">This code expires in 10 minutes.</p>
            </div>
        </body>
        </html>
        '''
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def is_valid_email_domain(email):
    if '@' not in email:
        return False
    domain = email.split('@')[1].lower()
    return domain in ALLOWED_EMAIL_DOMAINS

def generate_code():
    return ''.join(random.choices('0123456789', k=6))

@app.context_processor
def inject_settings():
    settings = {
        'discord_link': get_setting('discord_link'),
        'telegram_link': get_setting('telegram_link'),
        'youtube_link': get_setting('youtube_link'),
        'twitter_link': get_setting('twitter_link'),
        'website_name': get_setting('website_name', 'Moon.cc'),
        'resellers': get_all_resellers(),
        'cheats': get_all_cheats(),
        'coin_rate': int(get_setting('coin_rate', '98'))
    }
    return {'site_settings': settings}



@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('subscriptions'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        if user and user['password'] == password:
            session['user'] = username
            conn = get_db()
            c = conn.cursor()
            c.execute('UPDATE users SET last_ip = ?, last_login = ? WHERE username = ?',
                     (request.remote_addr, datetime.now().strftime('%Y-%m-%d %H:%M'), username))
            conn.commit()
            conn.close()
            track_stat('logins')
            return redirect(url_for('subscriptions'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
       
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
      
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
       
        if not is_valid_email_domain(email):
            flash('Only gmail.com, mail.com, ya.ru, yandex.ru emails are allowed', 'error')
            return render_template('register.html')
        
       
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            flash('Username or email already exists', 'error')
            return render_template('register.html')
        
       
        uid = int(get_setting('next_uid', '1'))
        
        # Создаем пользователя
        c.execute('''INSERT INTO users 
                    (username, password, email, email_verified, uid, joined, is_admin, ip, last_ip, last_login)
                    VALUES (?, ?, ?, 1, ?, ?, 0, ?, ?, ?)''',
                  (username, password, email, uid, 
                   datetime.now().strftime('%B %d, %Y'),
                   request.remote_addr, request.remote_addr, 
                   datetime.now().strftime('%Y-%m-%d %H:%M')))
        
        conn.commit()
        conn.close()
        
      
        set_setting('next_uid', str(uid + 1))
        
      
        track_stat('registrations')
        
        session['user'] = username
        
        flash('Registration successful! Welcome to Moon.cc!', 'success')
        return redirect(url_for('subscriptions'))
    
 
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/subscriptions')
@login_required
def subscriptions():
    user = get_user_by_username(session['user'])
    subs = get_user_subscriptions(user['id'])
    cheats = get_all_cheats()
    now = datetime.now()
    for sub in subs:
        if sub.get('expires'):
            try:
                exp = datetime.strptime(sub['expires'], '%Y-%m-%d %H:%M')
                sub['is_active'] = exp > now
                sub['days_left'] = max(0, (exp - now).days)
            except:
                sub['is_active'] = False
                sub['days_left'] = 0
        else:
            sub['is_active'] = False
            sub['days_left'] = 0
    user['subscriptions'] = subs
    return render_template('subscriptions.html', user=user, username=session['user'], cheats=cheats)

@app.route('/cloud', methods=['GET', 'POST'])
@login_required
def cloud():
    user = get_user_by_username(session['user'])
    has_sub = has_active_subscription(user['id'])
    
    if request.method == 'POST' and has_sub:
        action = request.form.get('action')
        conn = get_db()
        c = conn.cursor()
        
        if action == 'upload':
            now = datetime.now()
            hour_ago = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
            c.execute('SELECT COUNT(*) FROM configs WHERE author = ? AND uploaded > ?', (session['user'], hour_ago))
            if c.fetchone()[0] >= 3:
                flash('You can only upload 3 configs per hour', 'error')
            elif 'config_file' in request.files:
                file = request.files['config_file']
                if file and file.filename:
                    name = request.form.get('name', '').strip() or file.filename
                    description = request.form.get('description', '').strip()
                    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'cfg'
                    filename = f"config_{uuid.uuid4().hex[:8]}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    c.execute('INSERT INTO configs (name, description, filename, original_name, author, uploaded) VALUES (?, ?, ?, ?, ?, ?)',
                             (name, description, filename, file.filename, session['user'], now.strftime('%Y-%m-%d %H:%M')))
                    conn.commit()
                    flash('Config uploaded successfully', 'success')
        
        elif action == 'delete':
            config_id = int(request.form.get('config_id', 0))
            c.execute('SELECT * FROM configs WHERE id = ?', (config_id,))
            config = c.fetchone()
            if config and (config['author'] == session['user'] or user.get('is_admin')):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], config['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                c.execute('DELETE FROM configs WHERE id = ?', (config_id,))
                conn.commit()
                flash('Config deleted', 'success')
        conn.close()
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM configs ORDER BY uploaded DESC')
    configs = [dict(row) for row in c.fetchall()]
    conn.close()
    my_configs = [c for c in configs if c['author'] == session['user']]
    
    return render_template('cloud.html', user=user, username=session['user'],
                          has_subscription=has_sub, configs=configs, my_configs=my_configs)

@app.route('/cloud/download/<int:config_id>')
@login_required
def download_config(config_id):
    user = get_user_by_username(session['user'])
    if not has_active_subscription(user['id']):
        flash('You need an active subscription to download configs', 'error')
        return redirect(url_for('cloud'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM configs WHERE id = ?', (config_id,))
    config = c.fetchone()
    if config:
        c.execute('UPDATE configs SET downloads = downloads + 1 WHERE id = ?', (config_id,))
        conn.commit()
        conn.close()
        return send_from_directory(app.config['UPLOAD_FOLDER'], config['filename'],
                                  as_attachment=True, download_name=config['original_name'])
    conn.close()
    flash('Config not found', 'error')
    return redirect(url_for('cloud'))


@app.route('/roulette')
@login_required
def roulette():
    user = get_user_by_username(session['user'])
    cheats = [c for c in get_all_cheats() if c.get('active')]
    
    roulette_enabled = get_setting('roulette_enabled', '1') == '1'
    
    last_spin = user.get('last_spin', '')
    can_spin = True
    time_left = 0
    
    if last_spin:
        try:
            last_spin_time = datetime.strptime(last_spin, '%Y-%m-%d %H:%M')
            time_since = (datetime.now() - last_spin_time).total_seconds()
            if time_since < 86400:
                can_spin = False
                time_left = int(86400 - time_since)
        except:
            pass
    
    return render_template('roulette.html', user=user, username=session['user'],
                          cheats=cheats, can_spin=can_spin, time_left=time_left,
                          roulette_enabled=roulette_enabled)

@app.route('/roulette/spin', methods=['POST'])
@login_required
def spin_roulette():
    if get_setting('roulette_enabled', '1') != '1':
        return jsonify({'error': 'Roulette is currently disabled'}), 400
    
    user = get_user_by_username(session['user'])
    cheats = [c for c in get_all_cheats() if c.get('active')]
    
    if not cheats:
        return jsonify({'error': 'No cheats available'}), 400
    
    last_spin = user.get('last_spin', '')
    if last_spin:
        try:
            last_spin_time = datetime.strptime(last_spin, '%Y-%m-%d %H:%M')
            if (datetime.now() - last_spin_time).total_seconds() < 86400:
                return jsonify({'error': 'You can spin once every 24 hours'}), 400
        except:
            pass
    
    cheat = random.choice(cheats)
    days_weights = [(0, 20), (1, 25), (2, 20), (3, 15), (5, 10), (7, 5), (14, 3), (21, 1), (30, 1)]
    days_pool = []
    for d, w in days_weights:
        days_pool.extend([d] * w)
    days = random.choice(days_pool)
    
    coins_weights = [(0, 30), (5, 25), (10, 20), (15, 12), (25, 8), (50, 4), (100, 1)]
    coins_pool = []
    for c_val, w in coins_weights:
        coins_pool.extend([c_val] * w)
    bonus_coins = random.choice(coins_pool)
    
    conn = get_db()
    c = conn.cursor()
    

    if bonus_coins > 0:
        c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (bonus_coins, user['id']))
    
    if days > 0:

        c.execute('SELECT * FROM subscriptions WHERE user_id = ? AND cheat_id = ?', (user['id'], cheat['id']))
        existing_sub = c.fetchone()
        
        if existing_sub:

            try:
                current_expires = datetime.strptime(existing_sub['expires'], '%Y-%m-%d %H:%M')
                if current_expires > datetime.now():
                    new_expires = (current_expires + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                else:
                    new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            except:
                new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            c.execute('UPDATE subscriptions SET expires = ? WHERE id = ?', (new_expires, existing_sub['id']))
        else:

            expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            c.execute('INSERT INTO subscriptions (user_id, cheat_id, cheat_name, game, expires, activated, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (user['id'], cheat['id'], cheat['name'], cheat['game'], expires, datetime.now().strftime('%Y-%m-%d %H:%M'), 'roulette'))
    
    c.execute('UPDATE users SET last_spin = ? WHERE id = ?', (datetime.now().strftime('%Y-%m-%d %H:%M'), user['id']))
    conn.commit()
    conn.close()
    
    items = []
    possible_days = [0, 1, 2, 3, 5, 7, 14, 21, 30]
    for i in range(50):
        ch = random.choice(cheats)
        d = random.choice(possible_days)
        items.append({
            'cheat_name': ch['name'],
            'game': ch['game'],
            'icon': ch.get('icon', ch['name'][0]),
            'icon_type': ch.get('icon_type', 'text'),
            'days': d
        })
    
    items[45] = {
        'cheat_name': cheat['name'],
        'game': cheat['game'],
        'icon': cheat.get('icon', cheat['name'][0]),
        'icon_type': cheat.get('icon_type', 'text'),
        'days': days,
        'winner': True
    }
    
    return jsonify({
        'success': True,
        'items': items,
        'prize': {'cheat_name': cheat['name'], 'game': cheat['game'], 'days': days, 'coins': bonus_coins}
    })

@app.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    user = get_user_by_username(session['user'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        conn = get_db()
        c = conn.cursor()
        
        if action == 'change_password':
            old_pass = request.form.get('old_password')
            new_pass = request.form.get('new_password')
            confirm_pass = request.form.get('confirm_password')
            if old_pass == user['password'] and new_pass == confirm_pass:
                c.execute('UPDATE users SET password = ? WHERE id = ?', (new_pass, user['id']))
                conn.commit()
                flash('Password changed successfully', 'success')
            else:
                flash('Invalid password or passwords do not match', 'error')
        
        elif action == 'change_profile':
            new_nick = request.form.get('nickname', '').strip()
            bio = request.form.get('bio', '').strip()
            email = request.form.get('email', '').strip()
            
            if new_nick and new_nick != session['user']:
                c.execute('SELECT id FROM users WHERE username = ?', (new_nick,))
                if c.fetchone():
                    flash('Username already taken', 'error')
                else:
                    c.execute('UPDATE users SET username = ? WHERE id = ?', (new_nick, user['id']))
                    conn.commit()
                    session['user'] = new_nick
                    flash('Username changed successfully', 'success')
                    conn.close()
                    return redirect(url_for('security'))
            
            c.execute('UPDATE users SET bio = ?, email = ? WHERE id = ?', (bio, email, user['id']))
            conn.commit()
            flash('Profile updated', 'success')
        
        elif action == 'change_avatar':
            avatar_url = request.form.get('avatar_url', '').strip()
            if 'avatar_file' in request.files:
                file = request.files['avatar_file']
                if file and file.filename and allowed_file(file.filename, ALLOWED_EXTENSIONS):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"{session['user']}_{uuid.uuid4().hex[:8]}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    avatar_url = url_for('static', filename=f'uploads/{filename}')
            c.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_url, user['id']))
            conn.commit()
            flash('Avatar updated', 'success')
        
        conn.close()
    
    user = get_user_by_username(session['user'])
    return render_template('security.html', user=user, username=session['user'])

@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    user = get_user_by_username(session['user'])
    categories = get_all_categories()
    
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        category = request.form.get('category', '').strip()
        message = request.form.get('message', '').strip()
        
        if subject and message:
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO tickets (user_id, username, subject, category, message, status, created) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (user['id'], session['user'], subject, category, message, 'open', datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            conn.close()
            flash('Ticket submitted successfully', 'success')
            return redirect(url_for('support'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tickets WHERE username = ? ORDER BY created DESC', (session['user'],))
    tickets = {str(row['id']): dict(row) for row in c.fetchall()}
    conn.close()
    
    return render_template('support.html', user=user, username=session['user'], categories=categories, tickets=tickets)

@app.route('/support/ticket/<ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    user = get_user_by_username(session['user'])
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
    ticket = c.fetchone()
    
    if not ticket or (ticket['username'] != session['user'] and not user.get('is_admin')):
        conn.close()
        flash('Ticket not found', 'error')
        return redirect(url_for('support'))
    
    ticket = dict(ticket)
    
    if request.method == 'POST':
        reply = request.form.get('reply', '').strip()
        if reply:
            c.execute('INSERT INTO ticket_replies (ticket_id, username, message, date, is_admin) VALUES (?, ?, ?, ?, ?)',
                     (ticket_id, session['user'], reply, datetime.now().strftime('%Y-%m-%d %H:%M'), 1 if user.get('is_admin') else 0))
            
            if user.get('is_admin') and ticket['status'] == 'open':
                c.execute('UPDATE tickets SET status = ? WHERE id = ?', ('answered', ticket_id))
            elif not user.get('is_admin') and ticket['status'] == 'answered':
                c.execute('UPDATE tickets SET status = ? WHERE id = ?', ('open', ticket_id))
            
            conn.commit()
            flash('Reply sent', 'success')
    
    c.execute('SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY date', (ticket_id,))
    ticket['replies'] = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return render_template('ticket_view.html', user=user, username=session['user'], ticket=ticket, ticket_id=ticket_id)

@app.route('/download')
@login_required
def download():
    user = get_user_by_username(session['user'])
    has_sub = has_active_subscription(user['id'])
    loader = {
        'version': get_setting('loader_version', '1.0.0'),
        'filename': get_setting('loader_filename', '')
    }
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM changelog ORDER BY id DESC')
    loader['changelog'] = [{'version': row['version'], 'date': row['date'], 'changes': row['changes'].split('\n')} for row in c.fetchall()]
    conn.close()
    return render_template('download.html', user=user, username=session['user'], has_subscription=has_sub, loader=loader)

@app.route('/download/loader')
@login_required
def download_loader():
    user = get_user_by_username(session['user'])
    if not has_active_subscription(user['id']):
        flash('You need an active subscription to download', 'error')
        return redirect(url_for('download'))
    
    filename = get_setting('loader_filename', '')
    if not filename:
        flash('Loader not available', 'error')
        return redirect(url_for('download'))
    
    downloads = int(get_setting('downloads', '0'))
    set_setting('downloads', str(downloads + 1))
    
    return send_from_directory(
        app.config['LOADER_FOLDER'], 
        filename, 
        as_attachment=True
    )

@app.route('/activate', methods=['POST'])
@login_required
def activate_key():
    key = request.form.get('key', '').strip()
    user = get_user_by_username(session['user'])
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM keys WHERE key_code = ?', (key,))
    key_data = c.fetchone()
    
    if key_data:
        if key_data['used']:
            flash('This key has already been used', 'error')
        else:
            c.execute('SELECT * FROM cheats WHERE id = ?', (key_data['cheat_id'],))
            cheat = c.fetchone()
            if cheat:
                days = key_data['days']
                

                c.execute('SELECT * FROM subscriptions WHERE user_id = ? AND cheat_id = ?', (user['id'], cheat['id']))
                existing_sub = c.fetchone()
                
                if existing_sub:

                    try:
                        current_expires = datetime.strptime(existing_sub['expires'], '%Y-%m-%d %H:%M')
                        if current_expires > datetime.now():
                            new_expires = (current_expires + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                        else:
                            new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                    except:
                        new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                    
                    c.execute('UPDATE subscriptions SET expires = ? WHERE id = ?', (new_expires, existing_sub['id']))
                else:

                    expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                    c.execute('INSERT INTO subscriptions (user_id, cheat_id, cheat_name, game, expires, activated) VALUES (?, ?, ?, ?, ?, ?)',
                             (user['id'], cheat['id'], cheat['name'], cheat['game'], expires, datetime.now().strftime('%Y-%m-%d %H:%M')))
                
                c.execute('UPDATE keys SET used = 1, used_by = ?, used_at = ? WHERE key_code = ?',
                         (session['user'], datetime.now().strftime('%Y-%m-%d %H:%M'), key))
                conn.commit()
                keys_activated = int(get_setting('keys_activated', '0'))
                set_setting('keys_activated', str(keys_activated + 1))
                flash(f'Key activated! {cheat["name"]} for {days} days', 'success')
            else:
                flash('Invalid key', 'error')
    else:
        flash('Invalid key', 'error')
    
    conn.close()
    return redirect(url_for('subscriptions'))

@app.route('/claim-daily', methods=['POST'])
@login_required
def claim_daily():
    user = get_user_by_username(session['user'])
    daily_coins = int(get_setting('daily_coins', '10'))
    
    last_daily = user.get('last_daily', '')
    today = datetime.now().strftime('%Y-%m-%d')
    
    if last_daily:
        last_date = last_daily.split(' ')[0] if ' ' in last_daily else last_daily
        if last_date == today:
            return jsonify({'error': 'You already claimed your daily reward today'}), 400
        

        try:
            last_dt = datetime.strptime(last_date, '%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            if last_date == yesterday:

                new_streak = user.get('login_streak', 0) + 1
            else:

                new_streak = 1
        except:
            new_streak = 1
    else:
        new_streak = 1
    

    streak_bonus = min(new_streak * 5, 50)
    bonus_coins = int(daily_coins * streak_bonus / 100)
    total_coins = daily_coins + bonus_coins
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET coins = coins + ?, last_daily = ?, login_streak = ? WHERE id = ?',
             (total_coins, datetime.now().strftime('%Y-%m-%d %H:%M'), new_streak, user['id']))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'coins': total_coins,
        'base_coins': daily_coins,
        'bonus_coins': bonus_coins,
        'streak': new_streak,
        'new_balance': user.get('coins', 0) + total_coins
    })

@app.route('/buy-with-coins', methods=['POST'])
@login_required
def buy_with_coins():
    user = get_user_by_username(session['user'])
    cheat_id = request.form.get('cheat_id')
    days = int(request.form.get('days', 30))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (cheat_id,))
    cheat = c.fetchone()
    
    if not cheat:
        conn.close()
        flash('Product not found', 'error')
        return redirect(url_for('subscriptions'))
    
    if cheat['price'] <= 0:
        conn.close()
        flash('This product is free', 'error')
        return redirect(url_for('subscriptions'))
    

    coin_rate = int(get_setting('coin_rate', '98'))
    price_per_month = cheat['price']
    price_per_day = price_per_month / 30
    total_price_usd = price_per_day * days
    total_lc = int(total_price_usd * coin_rate)
    
    if user.get('coins', 0) < total_lc:
        conn.close()
        flash(f'Not enough LC coins. You need {total_lc} LC', 'error')
        return redirect(url_for('subscriptions'))
    

    c.execute('UPDATE users SET coins = coins - ? WHERE id = ?', (total_lc, user['id']))
    

    c.execute('SELECT * FROM subscriptions WHERE user_id = ? AND cheat_id = ?', (user['id'], cheat['id']))
    existing_sub = c.fetchone()
    
    if existing_sub:
        try:
            current_expires = datetime.strptime(existing_sub['expires'], '%Y-%m-%d %H:%M')
            if current_expires > datetime.now():
                new_expires = (current_expires + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            else:
                new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
        except:
            new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
        c.execute('UPDATE subscriptions SET expires = ? WHERE id = ?', (new_expires, existing_sub['id']))
    else:
        expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
        c.execute('INSERT INTO subscriptions (user_id, cheat_id, cheat_name, game, expires, activated, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (user['id'], cheat['id'], cheat['name'], cheat['game'], expires, datetime.now().strftime('%Y-%m-%d %H:%M'), 'coins'))
    
    conn.commit()
    conn.close()
    flash(f'{cheat["name"]} purchased for {total_lc} LC ({days} days)!', 'success')
    return redirect(url_for('subscriptions'))

@app.route('/activate-free', methods=['POST'])
@login_required
def activate_free_cheat():
    cheat_id = request.form.get('cheat_id')
    days = int(request.form.get('days', 7))
    user = get_user_by_username(session['user'])
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ? AND price = 0', (cheat_id,))
    cheat = c.fetchone()
    
    if cheat:

        c.execute('SELECT * FROM subscriptions WHERE user_id = ? AND cheat_id = ?', (user['id'], cheat['id']))
        existing_sub = c.fetchone()
        
        if existing_sub:

            try:
                current_expires = datetime.strptime(existing_sub['expires'], '%Y-%m-%d %H:%M')

                if current_expires > datetime.now():
                    new_expires = (current_expires + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                else:

                    new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            except:
                new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            
            c.execute('UPDATE subscriptions SET expires = ? WHERE id = ?', (new_expires, existing_sub['id']))
            conn.commit()
            flash(f'{cheat["name"]} extended by {days} days!', 'success')
        else:

            expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
            c.execute('INSERT INTO subscriptions (user_id, cheat_id, cheat_name, game, expires, activated, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (user['id'], cheat['id'], cheat['name'], cheat['game'], expires, datetime.now().strftime('%Y-%m-%d %H:%M'), 'free'))
            conn.commit()
            flash(f'{cheat["name"]} activated for {days} days!', 'success')
    else:
        flash('This product is not free', 'error')
    
    conn.close()
    return redirect(url_for('subscriptions'))

@app.route('/hwid-reset', methods=['POST'])
@login_required
def hwid_reset():
    user = get_user_by_username(session['user'])
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET hwid = ? WHERE id = ?', ('', user['id']))
    conn.commit()
    conn.close()
    flash('HWID Reset successful', 'success')
    return redirect(url_for('subscriptions'))

@app.route('/api/version', methods=['POST'])
@app.route('/api/version/', methods=['POST'])
def api_version():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = "loader_version"')
    existing_version = c.fetchone()
    conn.close()
    
    if existing_version:
        return '::ok::' + existing_version[0], 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        return '::error::Failed to find version columb =(', 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/api/hwid/<username>/<new_hwid>', methods=['POST'])
@app.route('/api/hwid/<username>/<new_hwid>/', methods=['POST'])
def api_hwid(username, new_hwid):
    try:
        force_param = request.args.get('force') or request.form.get('force')
        force_update = force_param and force_param.lower() == 'true'
        
        user = get_user_by_username(username)
        if not user:
            return '::error::User not found', 404, {'Content-Type': 'text/plain'}
        
        current_hwid = user.get('hwid', '')
        
        if current_hwid:
            if current_hwid == new_hwid:
                return '::ok::HWID already set and matches::' + current_hwid, 200, {'Content-Type': 'text/plain'}
            
            if not force_update:
                return '::error::HWID already exists::' + current_hwid, 403, {'Content-Type': 'text/plain'}
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE hwid = ? AND id != ?', (new_hwid, user['id']))
        existing_user = c.fetchone()
        
        if existing_user:
            conn.close()
            return '::error::HWID already in use::' + existing_user["username"], 409, {'Content-Type': 'text/plain'}
        
        c.execute('UPDATE users SET hwid = ? WHERE id = ?', (new_hwid, user['id']))
        conn.commit()
        conn.close()
        
        if current_hwid:
            return '::ok::HWID updated::' + current_hwid + '::' + new_hwid, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            return '::ok::HWID set::' + new_hwid, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        return '::error::' + str(e), 500, {'Content-Type': 'text/plain'}

@app.route('/api/keyless/strongspass/users/<username>/<password>', methods=['POST'])
@app.route('/api/keyless/strongspass/users/<username>/<password>/', methods=['POST'])
def api_user_raw(username, password):
    try:
        user = get_user_by_username(username)
        if not user:
            return 'User not found', 404, {'Content-Type': 'text/plain'}
        
        if password:
            if user['password'] != password:
                return 'Invalid password', 401, {'Content-Type': 'text/plain'}
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user['id'],))
        subs = c.fetchall()

        # Формат: Nickname//Password//AvatarUrl//JoinedDate//UID//LinkforThisSub1//ThisTimeSub1/...
        parts = [
            user['username'],
            user['password'] if password else '{no}',
            user['avatar'] or '{no}',
            user['joined'] or '{no}',
            str(user['uid'] or '{no}')
        ]
        
        for s in subs:
            c.execute('SELECT api_token FROM cheats WHERE id = ?', (s['cheat_id'],))
            cheat_row = c.fetchone()
            api_link = f"/api/cheat/{cheat_row['api_token']}" if cheat_row and cheat_row['api_token'] else ''
            parts.append(api_link)
            parts.append(s['expires'] or '')
        
        conn.close()
        return '::'.join(parts), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        return f'Error: {str(e)}', 500, {'Content-Type': 'text/plain'}

# API для получения данных чита по токену (RAW формат)
@app.route('/api/cheat/<token>', methods=['POST'])
def api_cheat_raw(token):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM cheats WHERE api_token = ?', (token,))
        cheat = c.fetchone()
        conn.close()
        
        if not cheat:
            return '::error::Cheat not found', 404, {'Content-Type': 'text/plain'}
        
        main_dll_url = f"/static/dlls/{cheat['main_dll']}" if cheat['main_dll'] else ''
        extra_dll_url = f"/static/dlls/{cheat['extra_dll']}" if cheat['extra_dll'] else ''

        # Формат: ::ok::name=value::name2=value2::...
        parts = [
            f'::ok::{cheat["name"]}',
            f'{cheat["game"]}',
            f'{cheat["cheat_type"]}',
            f'{cheat["price"]}',
            f'{cheat["active"]}',
            f'{main_dll_url}',
            f'{cheat["main_dll_process"]}',
            f'{cheat["main_dll_method"]}',
            f'{extra_dll_url}',
            f'{cheat["extra_dll_process"]}',
            f'{cheat["extra_dll_method"]}'
        ]
        
        return '::'.join(parts), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        return f'::error::{str(e)}', 500, {'Content-Type': 'text/plain'}
        
# API для скачивания DLL
@app.route('/api/dll/<token>/<dll_type>')
def api_download_dll(token, dll_type):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE api_token = ?', (token,))
    cheat = c.fetchone()
    conn.close()
    
    if not cheat:
        return 'Not found', 404
    
    if dll_type == 'main' and cheat['main_dll']:
        return send_from_directory(app.config['DLL_FOLDER'], cheat['main_dll'], as_attachment=True)
    elif dll_type == 'extra' and cheat['extra_dll']:
        return send_from_directory(app.config['DLL_FOLDER'], cheat['extra_dll'], as_attachment=True)
    
    return 'DLL not found', 404

# API для списка всех читов (RAW)
@app.route('/api/cheats')
@app.route('/api/cheats/')
def api_cheats_list():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM cheats WHERE active = 1')
        cheats = c.fetchall()
        conn.close()
        
        base_url = request.host_url.rstrip('/')
        lines = []
        for cheat in cheats:
            api_link = f"{base_url}/api/cheat/{cheat['api_token']}" if cheat['api_token'] else ''
            main_dll_url = f"{base_url}/static/dlls/{cheat['main_dll']}" if cheat['main_dll'] else ''
            extra_dll_url = f"{base_url}/static/dlls/{cheat['extra_dll']}" if cheat['extra_dll'] else ''
            
            line = f"{cheat['name']}::{cheat['game']}::{cheat['cheat_type']}::{cheat['price']}::{api_link}::{main_dll_url}::{extra_dll_url}"
            lines.append(line)
        
        return '\n'.join(lines) if lines else 'No cheats', 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f'Error: {str(e)}', 500, {'Content-Type': 'text/plain'}



@app.route('/admin')
@admin_required
def admin_panel():
    user = get_user_by_username(session['user'])
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM subscriptions')
    total_subs = c.fetchone()[0]
    
    chart_labels = []
    reg_data = []
    login_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        chart_labels.append((datetime.now() - timedelta(days=i)).strftime('%d.%m'))
        c.execute('SELECT count FROM stats WHERE stat_type = ? AND date = ?', ('registrations', day))
        row = c.fetchone()
        reg_data.append(row['count'] if row else 0)
        c.execute('SELECT count FROM stats WHERE stat_type = ? AND date = ?', ('logins', day))
        row = c.fetchone()
        login_data.append(row['count'] if row else 0)
    
    conn.close()
    
    stats = {
        'downloads': int(get_setting('downloads', '0')),
        'keys_activated': int(get_setting('keys_activated', '0'))
    }
    
    data = {'users': {}, 'settings': {'cheats': get_all_cheats()}}
    c2 = get_db().cursor()
    c2.execute('SELECT * FROM users')
    for u in c2.fetchall():
        data['users'][u['username']] = dict(u)
    
    return render_template('admin/dashboard.html',
        user=user, username=session['user'], data=data,
        chart_labels=chart_labels, reg_data=reg_data, login_data=login_data,
        total_subs=total_subs, stats=stats)

@app.route('/admin/users')
@admin_required
def admin_users():
    user = get_user_by_username(session['user'])
    cheats = get_all_cheats()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = {row['username']: dict(row) for row in c.fetchall()}
    for username in users:
        c.execute('SELECT * FROM subscriptions WHERE user_id = ?', (users[username]['id'],))
        users[username]['subscriptions'] = [dict(s) for s in c.fetchall()]
    conn.close()
    return render_template('admin/users.html', user=user, username=session['user'], users=users, cheats=cheats)

@app.route('/admin/users/<target_user>')
@admin_required
def admin_user_detail(target_user):
    user = get_user_by_username(session['user'])
    cheats = get_all_cheats()
    target = get_user_by_username(target_user)
    if not target:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    subs = get_user_subscriptions(target['id'])
    now = datetime.now()
    for sub in subs:
        if sub.get('expires'):
            try:
                exp = datetime.strptime(sub['expires'], '%Y-%m-%d %H:%M')
                sub['is_active'] = exp > now
            except:
                sub['is_active'] = False
    target['subscriptions'] = subs
    
    return render_template('admin/user_detail.html', user=user, username=session['user'],
                          target_user=target_user, target=target, cheats=cheats)

@app.route('/admin/users/<target_user>/give-sub', methods=['POST'])
@admin_required
def give_subscription(target_user):
    target = get_user_by_username(target_user)
    if target:
        cheat_id = int(request.form.get('cheat_id'))
        days = int(request.form.get('days', 30))
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM cheats WHERE id = ?', (cheat_id,))
        cheat = c.fetchone()
        if cheat:

            c.execute('SELECT * FROM subscriptions WHERE user_id = ? AND cheat_id = ?', (target['id'], cheat_id))
            existing_sub = c.fetchone()
            
            if existing_sub:

                try:
                    current_expires = datetime.strptime(existing_sub['expires'], '%Y-%m-%d %H:%M')
                    if current_expires > datetime.now():
                        new_expires = (current_expires + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                    else:
                        new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                except:
                    new_expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                c.execute('UPDATE subscriptions SET expires = ? WHERE id = ?', (new_expires, existing_sub['id']))
                flash(f'Subscription extended for {target_user} by {days} days', 'success')
            else:

                expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
                c.execute('INSERT INTO subscriptions (user_id, cheat_id, cheat_name, game, expires, activated, given_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (target['id'], cheat_id, cheat['name'], cheat['game'], expires, datetime.now().strftime('%Y-%m-%d %H:%M'), session['user']))
                flash(f'Subscription given to {target_user}', 'success')
            conn.commit()
        conn.close()
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/users/<target_user>/remove-sub/<int:sub_idx>', methods=['POST'])
@admin_required
def remove_subscription(target_user, sub_idx):
    target = get_user_by_username(target_user)
    if target:
        subs = get_user_subscriptions(target['id'])
        if 0 <= sub_idx < len(subs):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM subscriptions WHERE id = ?', (subs[sub_idx]['id'],))
            conn.commit()
            conn.close()
            flash('Subscription removed', 'success')
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/users/<target_user>/reset-roulette', methods=['POST'])
@admin_required
def reset_roulette_cooldown(target_user):
    target = get_user_by_username(target_user)
    if target:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE users SET last_spin = ? WHERE id = ?', ('', target['id']))
        conn.commit()
        conn.close()
        flash(f'Roulette cooldown reset for {target_user}', 'success')
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/users/<target_user>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(target_user):
    target = get_user_by_username(target_user)
    if target:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE users SET is_admin = ? WHERE id = ?', (0 if target['is_admin'] else 1, target['id']))
        conn.commit()
        conn.close()
        flash(f'Admin status toggled for {target_user}', 'success')
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/users/<target_user>/modify-coins', methods=['POST'])
@admin_required
def modify_user_coins(target_user):
    target = get_user_by_username(target_user)
    if target:
        action = request.form.get('action', 'add')
        amount = int(request.form.get('amount', 0))
        
        conn = get_db()
        c = conn.cursor()
        
        if action == 'add':
            c.execute('UPDATE users SET coins = coins + ? WHERE id = ?', (amount, target['id']))
            flash(f'Added {amount} LC to {target_user}', 'success')
        elif action == 'remove':
            c.execute('UPDATE users SET coins = MAX(0, coins - ?) WHERE id = ?', (amount, target['id']))
            flash(f'Removed {amount} LC from {target_user}', 'success')
        elif action == 'set':
            c.execute('UPDATE users SET coins = ? WHERE id = ?', (max(0, amount), target['id']))
            flash(f'Set {target_user} balance to {amount} LC', 'success')
        
        conn.commit()
        conn.close()
    return redirect(request.referrer or url_for('admin_user_detail', target_user=target_user))

@app.route('/admin/users/<target_user>/delete', methods=['POST'])
@admin_required
def delete_user(target_user):
    if target_user != session['user']:
        target = get_user_by_username(target_user)
        if target:
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (target['id'],))
            c.execute('DELETE FROM users WHERE id = ?', (target['id'],))
            conn.commit()
            conn.close()
            flash(f'User {target_user} deleted', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/cheats')
@admin_required
def admin_cheats():
    user = get_user_by_username(session['user'])
    return render_template('admin/cheats.html', user=user, username=session['user'], cheats=get_all_cheats())

@app.route('/admin/cheats/add', methods=['POST'])
@admin_required
def add_cheat():
    icon_type = request.form.get('icon_type', 'text')
    icon = request.form.get('icon', 'C')
    
    if icon_type == 'image':
        if 'icon_file' in request.files:
            file = request.files['icon_file']
            if file and file.filename and allowed_file(file.filename, ALLOWED_EXTENSIONS):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"cheat_{uuid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                icon = url_for('static', filename=f'uploads/{filename}')
            else:
                icon = request.form.get('icon_url', '')
        else:
            icon = request.form.get('icon_url', '')
    

    main_dll = ''
    if 'main_dll' in request.files:
        file = request.files['main_dll']
        if file and file.filename and file.filename.lower().endswith('.dll'):
            filename = f"main_{uuid.uuid4().hex[:8]}.dll"
            filepath = os.path.join(app.config['DLL_FOLDER'], filename)
            file.save(filepath)
            main_dll = filename
    

    extra_dll = ''
    if 'extra_dll' in request.files:
        file = request.files['extra_dll']
        if file and file.filename and file.filename.lower().endswith('.dll'):
            filename = f"extra_{uuid.uuid4().hex[:8]}.dll"
            filepath = os.path.join(app.config['DLL_FOLDER'], filename)
            file.save(filepath)
            extra_dll = filename
    

    api_token = uuid.uuid4().hex[:16]
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO cheats (game, name, icon, icon_type, price, active, cheat_type, 
                 main_dll, main_dll_process, main_dll_method, extra_dll, extra_dll_process, 
                 extra_dll_method, api_token) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (request.form.get('game'), 
              request.form.get('name'), 
              icon, 
              icon_type, 
              float(request.form.get('price', 0)),
              request.form.get('cheat_type', 'crack'),
              main_dll,
              request.form.get('main_dll_process', ''),
              request.form.get('main_dll_method', 'LoadLibrary'),
              extra_dll,
              request.form.get('extra_dll_process', ''),
              request.form.get('extra_dll_method', 'LoadLibrary'),
              api_token))
    conn.commit()
    conn.close()
    flash('Cheat added', 'success')
    return redirect(url_for('admin_cheats'))

@app.route('/admin/cheats/<int:cheat_id>/delete', methods=['POST'])
@admin_required
def delete_cheat(cheat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM cheats WHERE id = ?', (cheat_id,))
    conn.commit()
    conn.close()
    flash('Cheat deleted', 'success')
    return redirect(url_for('admin_cheats'))

@app.route('/admin/cheats/<int:cheat_id>/toggle', methods=['POST'])
@admin_required
def toggle_cheat(cheat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT active FROM cheats WHERE id = ?', (cheat_id,))
    cheat = c.fetchone()
    if cheat:
        c.execute('UPDATE cheats SET active = ? WHERE id = ?', (0 if cheat['active'] else 1, cheat_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_cheats'))

@app.route('/admin/cheats/<int:cheat_id>/edit', methods=['POST'])
@admin_required
def edit_cheat(cheat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (cheat_id,))
    cheat = c.fetchone()
    
    if not cheat:
        flash('Cheat not found', 'error')
        conn.close()
        return redirect(url_for('admin_cheats'))
    
    icon_type = request.form.get('icon_type', cheat['icon_type'])
    icon = cheat['icon']
    
    if icon_type == 'image':
        if 'icon_file' in request.files:
            file = request.files['icon_file']
            if file and file.filename and allowed_file(file.filename, ALLOWED_EXTENSIONS):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"cheat_{uuid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                icon = url_for('static', filename=f'uploads/{filename}')
        elif request.form.get('icon_url'):
            icon = request.form.get('icon_url', '')
    else:
        icon = request.form.get('icon', icon)
    
    main_dll = cheat['main_dll']
    if 'main_dll' in request.files:
        file = request.files['main_dll']
        if file and file.filename and file.filename.lower().endswith('.dll'):
            filename = f"main_{uuid.uuid4().hex[:8]}.dll"
            filepath = os.path.join(app.config['DLL_FOLDER'], filename)
            file.save(filepath)
            main_dll = filename
    
    extra_dll = cheat['extra_dll']
    if 'extra_dll' in request.files:
        file = request.files['extra_dll']
        if file and file.filename and file.filename.lower().endswith('.dll'):
            filename = f"extra_{uuid.uuid4().hex[:8]}.dll"
            filepath = os.path.join(app.config['DLL_FOLDER'], filename)
            file.save(filepath)
            extra_dll = filename
    
    c.execute('''UPDATE cheats SET game=?, name=?, icon=?, icon_type=?, price=?, cheat_type=?,
                 main_dll=?, main_dll_process=?, main_dll_method=?,
                 extra_dll=?, extra_dll_process=?, extra_dll_method=?
                 WHERE id=?''',
             (request.form.get('game'),
              request.form.get('name'),
              icon,
              icon_type,
              float(request.form.get('price', 0)),
              request.form.get('cheat_type', 'crack'),
              main_dll,
              request.form.get('main_dll_process', ''),
              request.form.get('main_dll_method', 'LoadLibrary'),
              extra_dll,
              request.form.get('extra_dll_process', ''),
              request.form.get('extra_dll_method', 'LoadLibrary'),
              cheat_id))
    conn.commit()
    conn.close()
    flash('Cheat updated', 'success')
    return redirect(url_for('admin_cheats'))

@app.route('/admin/keys')
@admin_required
def admin_keys():
    user = get_user_by_username(session['user'])
    cheats = get_all_cheats()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM keys ORDER BY created DESC')
    keys = {row['key_code']: dict(row) for row in c.fetchall()}
    conn.close()
    return render_template('admin/keys.html', user=user, username=session['user'], cheats=cheats, keys=keys)

@app.route('/admin/keys/generate', methods=['POST'])
@admin_required
def generate_keys():
    cheat_id = int(request.form.get('cheat_id'))
    days = int(request.form.get('days', 30))
    count = int(request.form.get('count', 1))
    prefix = request.form.get('prefix', 'RT')
    
    conn = get_db()
    c = conn.cursor()
    for _ in range(min(count, 100)):
        key = f"{prefix}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}"
        c.execute('INSERT INTO keys (key_code, cheat_id, days, created, created_by, used) VALUES (?, ?, ?, ?, ?, 0)',
                 (key, cheat_id, days, datetime.now().strftime('%Y-%m-%d %H:%M'), session['user']))
    conn.commit()
    conn.close()
    flash(f'Generated {min(count, 100)} keys', 'success')
    return redirect(url_for('admin_keys'))

@app.route('/admin/keys/<key>/delete', methods=['POST'])
@admin_required
def delete_key(key):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM keys WHERE key_code = ?', (key,))
    conn.commit()
    conn.close()
    flash('Key deleted', 'success')
    return redirect(url_for('admin_keys'))


@app.route('/admin/loader', methods=['GET', 'POST'])
@admin_required
def admin_loader():
    user = get_user_by_username(session['user'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'upload':
            if 'loader_file' in request.files:
                file = request.files['loader_file']
                if file and file.filename and allowed_file(file.filename, LOADER_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['LOADER_FOLDER'], filename)
                    file.save(filepath)
                    set_setting('loader_filename', filename)
                    flash('Loader uploaded successfully', 'success')
                else:
                    flash('Invalid file type. Allowed: exe, zip, rar', 'error')
        
        elif action == 'update_version':
            version = request.form.get('version', '').strip()
            if version:
                set_setting('loader_version', version)
                flash('Version updated', 'success')
        
        elif action == 'add_changelog':
            version = request.form.get('changelog_version', '').strip()
            date = request.form.get('changelog_date', '').strip() or datetime.now().strftime('%B %d, %Y')
            changes = request.form.get('changelog_changes', '').strip()
            if version and changes:
                conn = get_db()
                c = conn.cursor()
                c.execute('INSERT INTO changelog (version, date, changes) VALUES (?, ?, ?)', (version, date, changes))
                conn.commit()
                conn.close()
                flash('Changelog added', 'success')
        
        elif action == 'delete_changelog':
            idx = int(request.form.get('idx', -1))
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT id FROM changelog ORDER BY id DESC')
            rows = c.fetchall()
            if 0 <= idx < len(rows):
                c.execute('DELETE FROM changelog WHERE id = ?', (rows[idx]['id'],))
                conn.commit()
            conn.close()
            flash('Changelog deleted', 'success')
    
    loader = {
        'version': get_setting('loader_version', '1.0.0'),
        'filename': get_setting('loader_filename', '')
    }
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM changelog ORDER BY id DESC')
    loader['changelog'] = [{'version': row['version'], 'date': row['date'], 'changes': row['changes'].split('\n')} for row in c.fetchall()]
    conn.close()
    
    return render_template('admin/loader.html', user=user, username=session['user'], loader=loader)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    user = get_user_by_username(session['user'])
    
    if request.method == 'POST':
        set_setting('discord_link', request.form.get('discord_link', ''))
        set_setting('telegram_link', request.form.get('telegram_link', ''))
        set_setting('youtube_link', request.form.get('youtube_link', ''))
        set_setting('twitter_link', request.form.get('twitter_link', ''))
        set_setting('website_name', request.form.get('website_name', 'Moon.cc'))
        set_setting('roulette_enabled', '1' if request.form.get('roulette_enabled') else '0')
        set_setting('invite_required', '1' if request.form.get('invite_required') else '0')
        set_setting('coin_rate', request.form.get('coin_rate', '98'))
        set_setting('daily_coins', request.form.get('daily_coins', '10'))
        flash('Settings saved', 'success')
    
    settings = {
        'discord_link': get_setting('discord_link'),
        'telegram_link': get_setting('telegram_link'),
        'youtube_link': get_setting('youtube_link'),
        'twitter_link': get_setting('twitter_link'),
        'website_name': get_setting('website_name', 'Moon.cc'),
        'roulette_enabled': get_setting('roulette_enabled', '1'),
        'invite_required': get_setting('invite_required', '0'),
        'coin_rate': get_setting('coin_rate', '98'),
        'daily_coins': get_setting('daily_coins', '10')
    }
    
    return render_template('admin/settings.html', user=user, username=session['user'], settings=settings)

@app.route('/admin/api-docs')
@admin_required
def admin_api_docs():
    user = get_user_by_username(session['user'])
    cheats = get_all_cheats()
    base_url = request.host_url.rstrip('/')
    return render_template('admin/api_docs.html', user=user, username=session['user'], cheats=cheats, base_url=base_url)

@app.route('/admin/invites')
@admin_required
def admin_invites():
    user = get_user_by_username(session['user'])
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM invite_codes ORDER BY id DESC')
    invites = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template('admin/invites.html', user=user, username=session['user'], invites=invites)

@app.route('/admin/invites/generate', methods=['POST'])
@admin_required
def generate_invites():
    prefix = request.form.get('prefix', 'INV')
    max_uses = int(request.form.get('max_uses', 1))
    count = min(int(request.form.get('count', 1)), 50)
    
    conn = get_db()
    c = conn.cursor()
    for _ in range(count):
        code = f"{prefix}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))}"
        c.execute('INSERT INTO invite_codes (code, created, created_by, max_uses, uses, active) VALUES (?, ?, ?, ?, 0, 1)',
                 (code, datetime.now().strftime('%Y-%m-%d %H:%M'), session['user'], max_uses))
    conn.commit()
    conn.close()
    flash(f'Generated {count} invite codes', 'success')
    return redirect(url_for('admin_invites'))

@app.route('/admin/invites/<int:invite_id>/toggle', methods=['POST'])
@admin_required
def toggle_invite(invite_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT active FROM invite_codes WHERE id = ?', (invite_id,))
    invite = c.fetchone()
    if invite:
        c.execute('UPDATE invite_codes SET active = ? WHERE id = ?', (0 if invite['active'] else 1, invite_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_invites'))

@app.route('/admin/invites/<int:invite_id>/delete', methods=['POST'])
@admin_required
def delete_invite(invite_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM invite_codes WHERE id = ?', (invite_id,))
    conn.commit()
    conn.close()
    flash('Invite code deleted', 'success')
    return redirect(url_for('admin_invites'))

@app.route('/admin/resellers', methods=['GET', 'POST'])
@admin_required
def admin_resellers():
    user = get_user_by_username(session['user'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO resellers (name, flag, link) VALUES (?, ?, ?)',
                     (request.form.get('name'), request.form.get('flag', ''), request.form.get('link', '#')))
            conn.commit()
            conn.close()
            flash('Reseller added', 'success')
    
    return render_template('admin/resellers.html', user=user, username=session['user'], resellers=get_all_resellers())

@app.route('/admin/resellers/<int:idx>/delete', methods=['POST'])
@admin_required
def delete_reseller(idx):
    resellers = get_all_resellers()
    if 0 <= idx < len(resellers):
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM resellers WHERE id = ?', (resellers[idx]['id'],))
        conn.commit()
        conn.close()
        flash('Reseller deleted', 'success')
    return redirect(url_for('admin_resellers'))

@app.route('/admin/tickets')
@admin_required
def admin_tickets():
    user = get_user_by_username(session['user'])
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tickets ORDER BY created DESC')
    tickets = {str(row['id']): dict(row) for row in c.fetchall()}
    conn.close()
    categories = get_all_categories()
    return render_template('admin/tickets.html', user=user, username=session['user'], tickets=tickets, categories=categories)

@app.route('/admin/tickets/<ticket_id>/close', methods=['POST'])
@admin_required
def close_ticket(ticket_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE tickets SET status = ? WHERE id = ?', ('closed', ticket_id))
    conn.commit()
    conn.close()
    flash('Ticket closed', 'success')
    return redirect(request.referrer or url_for('admin_tickets'))

@app.route('/admin/tickets/<ticket_id>/delete', methods=['POST'])
@admin_required
def delete_ticket(ticket_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM ticket_replies WHERE ticket_id = ?', (ticket_id,))
    c.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()
    flash('Ticket deleted', 'success')
    return redirect(url_for('admin_tickets'))

@app.route('/admin/tickets/categories', methods=['POST'])
@admin_required
def manage_categories():
    action = request.form.get('action')
    conn = get_db()
    c = conn.cursor()
    
    if action == 'add':
        name = request.form.get('name', '').strip()
        if name:
            c.execute('INSERT INTO ticket_categories (name) VALUES (?)', (name,))
            conn.commit()
            flash('Category added', 'success')
    
    elif action == 'delete':
        idx = int(request.form.get('idx', -1))
        c.execute('SELECT id FROM ticket_categories')
        cats = c.fetchall()
        if 0 <= idx < len(cats):
            c.execute('DELETE FROM ticket_categories WHERE id = ?', (cats[idx]['id'],))
            conn.commit()
            flash('Category deleted', 'success')
    
    conn.close()
    return redirect(url_for('admin_tickets'))


@app.route('/terms')
@login_required
def terms():
    user = get_user_by_username(session['user'])
    return render_template('terms.html', user=user, username=session['user'])

@app.route('/privacy')
@login_required
def privacy():
    user = get_user_by_username(session['user'])
    return render_template('privacy.html', user=user, username=session['user'])

@app.route('/refund')
@login_required
def refund():
    user = get_user_by_username(session['user'])
    return render_template('refund.html', user=user, username=session['user'])
@app.route('/check-users')
def check_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, password, email FROM users")
    users = c.fetchall()
    result = "<h3>Пользователи в базе данных на Replit:</h3>"
    result += "<table border='1'><tr><th>Username</th><th>Password</th><th>Email</th></tr>"
    for u in users:
        result += f"<tr><td>{u['username']}</td><td>{u['password']}</td><td>{u['email']}</td></tr>"
    result += "</table>"
    conn.close()
    return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
