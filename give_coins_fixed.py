# give_coins_fixed.py
from __init__ import get_db

# Укажите данные
username = "arellugly"  # ИЗМЕНИТЕ на имя нужного пользователя
coins_to_add = 10000     # сколько монет выдать

# Подключаемся к БД
conn = get_db()
c = conn.cursor()

# Проверяем, существует ли пользователь
c.execute("SELECT id, username, coins FROM users WHERE username = ?", (username,))
user = c.fetchone()

if user:
    # Добавляем монеты
    new_balance = user['coins'] + coins_to_add
    c.execute("UPDATE users SET coins = ? WHERE id = ?", (new_balance, user['id']))
    conn.commit()
    print(f"✅ Выдано {coins_to_add} LC монет пользователю {username}")
    print(f"💰 Текущий баланс: {user['coins']} → {new_balance} LC")
else:
    print(f"❌ Пользователь {username} не найден")
    print("\n📋 Доступные пользователи:")
    c.execute("SELECT username, coins FROM users")
    for u in c.fetchall():
        print(f"   - {u['username']}: {u['coins']} LC")

conn.close()