import os
import shutil
from flask import Flask, render_template, url_for
from flask_frozen import Freezer

# Создаем упрощенное приложение
app = Flask(__name__, 
            template_folder='static_templates',  # используем наши упрощенные шаблоны
            static_folder='static')  # статические файлы из оригинальной папки

# Настройки
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_DESTINATION'] = 'build'
app.config['FREEZER_REMOVE_EXTRA_FILES'] = True

# Игнорируем предупреждения
import warnings
warnings.filterwarnings('ignore')

# Маршруты
@app.route('/')
def index():
    return render_template('login.html')  # используем статическую версию login

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/refund')
def refund():
    return render_template('refund.html')

# Копируем оригинальный login.html и register.html
def copy_auth_templates():
    # Создаем простые версии login и register
    login_content = '''
{% extends "base.html" %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="auth-container">
    <div class="auth-box">
        <div class="auth-logo">
            <img src="{{ url_for('static', filename='CompImage/png.png') }}" alt="Phook+" class="auth-logo-img">
        </div>
        
        <h2>Login</h2>
        <form method="POST" class="auth-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="input-field" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="input-field" required>
            </div>
            <button type="submit" class="btn btn-primary btn-full">Login</button>
        </form>
        <p class="auth-link">Don't have an account? <a href="/register">Register</a></p>
    </div>
</div>
{% endblock %}
'''
    
    register_content = '''
{% extends "base.html" %}

{% block title %}Register{% endblock %}

{% block content %}
<div class="auth-container">
    <div class="auth-box">
        <div class="auth-logo">
            <img src="{{ url_for('static', filename='CompImage/png.png') }}" alt="Phook+" class="auth-logo-img">
        </div>
        
        <h2>Create Account</h2>
        <form method="POST" class="auth-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="input-field" required minlength="3">
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" class="input-field" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="input-field" required minlength="6">
            </div>
            <button type="submit" class="btn btn-primary btn-full">Register</button>
        </form>
        <p class="auth-link">Already have an account? <a href="/login">Login</a></p>
    </div>
</div>
{% endblock %}
'''
    
    # Сохраняем файлы
    with open(os.path.join('static_templates', 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login_content)
    
    with open(os.path.join('static_templates', 'register.html'), 'w', encoding='utf-8') as f:
        f.write(register_content)

freezer = Freezer(app)

if __name__ == '__main__':
    print("🚀 Подготавливаем статические шаблоны...")
    
    # Создаем папку для шаблонов если её нет
    os.makedirs('static_templates', exist_ok=True)
    
    # Копируем шаблоны
    copy_auth_templates()
    
    # Удаляем старую папку build
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("🧹 Старая папка build удалена")
    
    print("📦 Замораживаем статический сайт...")
    freezer.freeze()
    
    # Копируем статические файлы
    static_src = os.path.join(os.path.dirname(__file__), 'static')
    static_dst = os.path.join('build', 'static')
    if os.path.exists(static_src):
        if os.path.exists(static_dst):
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print("📁 Статические файлы скопированы")
    
    print(f"✅ Готово! Статический сайт в папке: {os.path.abspath('build')}")
    print("\n📋 Созданные страницы:")
    for root, dirs, files in os.walk('build'):
        for file in files:
            if file.endswith('.html'):
                print(f"   - {os.path.join(root, file)}")