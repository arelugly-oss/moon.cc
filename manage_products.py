import sqlite3
import os
import uuid

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASEDIR, 'database.db')

print(f'Путь к базе данных: {DATABASE}')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ща секу"""
    conn = get_db()
    c = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    print('База данных найдена, теперь хуярь что нужно')

def list_products():
    """Показать все продукты"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats ORDER BY id')
    products = c.fetchall()
    conn.close()
    
    if not products:
        print('\nПродуктов пока нет.\n')
        return
    
    print('\nСписок продуктов:')
    print('=' * 80)
    for p in products:
        status = 'Активен' if p['active'] else 'Отключен'
        price_str = f"${p['price']}" if p['price'] > 0 else 'БЕСПЛАТНО'
        print(f"\nID: {p['id']}")
        print(f"  Название: {p['name']}")
        print(f"  Игра: {p['game']}")
        print(f"  Цена: {price_str}")
        print(f"  Тип: {p['cheat_type']}")
        print(f"  Иконка: {p['icon']} (тип: {p['icon_type']})")
        print(f"  API Token: {p['api_token'] or 'не установлен'}")
        print(f"  Статус: {status}")
    print('=' * 80)
    print(f'Всего: {len(products)} продуктов\n')

def add_product():
    """Добавить новый продукт"""
    print('\nДобавление нового продукта\n')
    
    name = input('Название продукта: ').strip()
    if not name:
        print('Название обязательно!')
        return
    
    game = input('Название игры: ').strip()
    if not game:
        print('Название игры обязательно!')
        return
    
    price_input = input('Цена в USD (0 для бесплатного): ').strip()
    try:
        price = float(price_input) if price_input else 0
    except:
        price = 0
    
    print('\nТип чита:')
    print('1. Release (релиз)')
    print('2. Crack (кряк)')
    type_choice = input('Выбор (1-2) [2]: ').strip() or '2'
    cheat_type = 'release' if type_choice == '1' else 'crack'
    
    print('\nИконка:')
    print('1. Текст (первая буква названия)')
    print('2. Emoji')
    print('3. URL изображения')
    icon_choice = input('Выбор (1-3) [1]: ').strip() or '1'
    
    if icon_choice == '1':
        icon = name[0].upper()
        icon_type = 'text'
    elif icon_choice == '2':
        icon = input('Введите emoji: ').strip() or 'G'
        icon_type = 'emoji'
    else:
        icon = input('URL изображения: ').strip()
        icon_type = 'image'
    
    active_input = input('Активен? (y/n) [y]: ').strip().lower()
    active = 0 if active_input == 'n' else 1
    
    api_token = str(uuid.uuid4())
    
    print('\nDLL настройки (оставьте пустым если не нужно):')
    main_dll = input('Main DLL filename: ').strip()
    main_dll_process = input('Main DLL process name: ').strip()
    main_dll_method = input('Main DLL method (LoadLibrary/ManualMap) [LoadLibrary]: ').strip() or 'LoadLibrary'
    
    extra_dll = input('Extra DLL filename: ').strip()
    extra_dll_process = input('Extra DLL process name: ').strip()
    extra_dll_method = input('Extra DLL method (LoadLibrary/ManualMap) [LoadLibrary]: ').strip() or 'LoadLibrary'
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO cheats 
        (name, game, price, cheat_type, icon, icon_type, active, api_token,
         main_dll, main_dll_process, main_dll_method,
         extra_dll, extra_dll_process, extra_dll_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (name, game, price, cheat_type, icon, icon_type, active, api_token,
         main_dll, main_dll_process, main_dll_method,
         extra_dll, extra_dll_process, extra_dll_method))
    conn.commit()
    product_id = c.lastrowid
    conn.close()
    
    print(f'\nПродукт "{name}" добавлен! ID: {product_id}')
    print(f'API Token: {api_token}')

def edit_product():
    """Редактировать продукт"""
    list_products()
    
    product_id = input('\nВведите ID продукта для редактирования: ').strip()
    if not product_id.isdigit():
        print('Неверный ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (int(product_id),))
    product = c.fetchone()
    
    if not product:
        print(f'Продукт с ID {product_id} не найден!')
        conn.close()
        return
    
    print(f'\nРедактирование: {product["name"]}')
    print('(Оставьте пустым чтобы не менять)\n')
    
    name = input(f'Название [{product["name"]}]: ').strip() or product['name']
    game = input(f'Игра [{product["game"]}]: ').strip() or product['game']
    
    price_input = input(f'Цена [{product["price"]}]: ').strip()
    price = float(price_input) if price_input else product['price']
    
    print(f'\nТекущий тип: {product["cheat_type"]}')
    print('1. Release (релиз)')
    print('2. Crack (кряк)')
    type_input = input('Изменить тип? (1/2 или Enter чтобы не менять): ').strip()
    if type_input == '1':
        cheat_type = 'release'
    elif type_input == '2':
        cheat_type = 'crack'
    else:
        cheat_type = product['cheat_type']
    
    print(f'\nТекущая иконка: {product["icon"]} (тип: {product["icon_type"]})')
    change_icon = input('Изменить иконку? (y/n) [n]: ').strip().lower()
    
    if change_icon == 'y':
        print('1. Текст')
        print('2. Emoji')
        print('3. URL изображения')
        icon_choice = input('Выбор (1-3): ').strip()
        
        if icon_choice == '1':
            icon = input('Текст: ').strip() or name[0].upper()
            icon_type = 'text'
        elif icon_choice == '2':
            icon = input('Emoji: ').strip() or '🎮'
            icon_type = 'emoji'
        elif icon_choice == '3':
            icon = input('URL: ').strip()
            icon_type = 'image'
        else:
            icon = product['icon']
            icon_type = product['icon_type']
    else:
        icon = product['icon']
        icon_type = product['icon_type']
    
    active_input = input(f'Активен? (y/n) [{"y" if product["active"] else "n"}]: ').strip().lower()
    if active_input:
        active = 0 if active_input == 'n' else 1
    else:
        active = product['active']
    
    print('\nDLL настройки:')
    main_dll = input(f'Main DLL [{product["main_dll"]}]: ').strip() or product['main_dll']
    main_dll_process = input(f'Main DLL process [{product["main_dll_process"]}]: ').strip() or product['main_dll_process']
    main_dll_method = input(f'Main DLL method [{product["main_dll_method"]}]: ').strip() or product['main_dll_method']
    
    extra_dll = input(f'Extra DLL [{product["extra_dll"]}]: ').strip() or product['extra_dll']
    extra_dll_process = input(f'Extra DLL process [{product["extra_dll_process"]}]: ').strip() or product['extra_dll_process']
    extra_dll_method = input(f'Extra DLL method [{product["extra_dll_method"]}]: ').strip() or product['extra_dll_method']
    
    c.execute('''UPDATE cheats SET 
        name=?, game=?, price=?, cheat_type=?, icon=?, icon_type=?, active=?,
        main_dll=?, main_dll_process=?, main_dll_method=?,
        extra_dll=?, extra_dll_process=?, extra_dll_method=?
        WHERE id=?''',
        (name, game, price, cheat_type, icon, icon_type, active,
         main_dll, main_dll_process, main_dll_method,
         extra_dll, extra_dll_process, extra_dll_method,
         int(product_id)))
    conn.commit()
    conn.close()
    
    print(f'\nПродукт "{name}" обновлен!')

def delete_product():
    """Удалить продукт"""
    list_products()
    
    product_id = input('\nВведите ID продукта для удаления: ').strip()
    if not product_id.isdigit():
        print('Неверный ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (int(product_id),))
    product = c.fetchone()
    
    if not product:
        print(f'Продукт с ID {product_id} не найден!')
        conn.close()
        return
    
    confirm = input(f'\nУдалить "{product["name"]}"? (yes/no): ').strip().lower()
    if confirm != 'yes':
        print('Отменено')
        conn.close()
        return
    
    c.execute('DELETE FROM cheats WHERE id = ?', (int(product_id),))
    conn.commit()
    conn.close()
    
    print(f'\nПродукт "{product["name"]}" удален!')

def toggle_status():
    """Включить/выключить продукт"""
    list_products()
    
    product_id = input('\nВведите ID продукта: ').strip()
    if not product_id.isdigit():
        print('Неверный ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (int(product_id),))
    product = c.fetchone()
    
    if not product:
        print(f'Продукт с ID {product_id} не найден!')
        conn.close()
        return
    
    new_status = 0 if product['active'] else 1
    c.execute('UPDATE cheats SET active = ? WHERE id = ?', (new_status, int(product_id)))
    conn.commit()
    conn.close()
    
    status_text = 'активирован' if new_status else 'деактивирован'
    print(f'\nПродукт "{product["name"]}" {status_text}!')

def show_api_info():
    """Показать API информацию"""
    list_products()
    
    product_id = input('\nВведите ID продукта: ').strip()
    if not product_id.isdigit():
        print('Неверный ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM cheats WHERE id = ?', (int(product_id),))
    product = c.fetchone()
    conn.close()
    
    if not product:
        print(f'Продукт с ID {product_id} не найден!')
        return
    
    print(f'\nAPI информация для "{product["name"]}":')
    print('=' * 60)
    print(f'API Token: {product["api_token"]}')
    print(f'API URL: /api/cheat/{product["api_token"]}')
    print(f'Main DLL: {product["main_dll"]}')
    print(f'Main DLL Process: {product["main_dll_process"]}')
    print(f'Main DLL Method: {product["main_dll_method"]}')
    print(f'Extra DLL: {product["extra_dll"]}')
    print(f'Extra DLL Process: {product["extra_dll_process"]}')
    print(f'Extra DLL Method: {product["extra_dll_method"]}')
    print('=' * 60)

if __name__ == '__main__':
    print('\nСюда писи попи\n')
    
    if os.path.exists(DATABASE):
        print(f'Файл БД найден: {DATABASE}')
    else:
        print(f'Файл БД не найден, будет создан: {DATABASE}')
    
    init_db()
    
    while True:
        print('\n' + '=' * 60)
        print('Выберите действие:')
        print('1. Показать все продукты')
        print('2. Добавить продукт')
        print('3. Редактировать продукт')
        print('4. Удалить продукт')
        print('5. Включить/выключить продукт')
        print('6. Показать API информацию')
        print('7. Выход')
        print('=' * 60)
        
        choice = input('\nВаш выбор (1-7): ').strip()
        
        if choice == '1':
            list_products()
        elif choice == '2':
            add_product()
        elif choice == '3':
            edit_product()
        elif choice == '4':
            delete_product()
        elif choice == '5':
            toggle_status()
        elif choice == '6':
            show_api_info()
        elif choice == '7':
            print('\nДо свидания!')
            break
        else:
            print('Неверный выбор')
