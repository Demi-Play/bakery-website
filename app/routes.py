from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import get_db_connection
from .forms import RegisterForm, LoginForm, ProductForm

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search', '')
    sort_option = request.form.get('sort', 'name')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    if search_query:
        products = [product for product in products if search_query.lower() in product['name'].lower()]
    
    products.sort(key=lambda x: x[sort_option])

    return render_template('index.html', products=products)

@bp.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search', '')
    sort_option = request.form.get('sort', 'name')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM Product")
        products = cursor.fetchall()

        if search_query:
            products = [product for product in products if search_query.lower() in product['name'].lower()]

        products.sort(key=lambda x: x[sort_option])
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        products = []
    finally:
        cursor.close()
        connection.close()

    return render_template('index.html', products=products)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("INSERT INTO User (username, email, password) VALUES (%s, %s, %s)", 
                           (username, email, generate_password_hash(password)))
            connection.commit()
            flash('Регистрация успешна. Войдите в свою учетную запись.')
            return redirect(url_for('main.login'))
        except Exception as e:
            connection.rollback()
            print(f"Ошибка при записи в БД: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print(form.errors)

    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data
        password = form.password.data

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and check_password_hash(user['password'], password):
            login_user(user)
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неправильное имя пользователя или пароль.', 'danger')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Product WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('product_detail.html', product=product)

@bp.route('/cart')
@login_required
def cart():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Cart WHERE user_id = %s", (current_user.id,))
    cart = cursor.fetchone()
    cursor.close()
    connection.close()

    total_price = 0.0
    if cart and cart['items']:
        total_price = sum(item['price'] * item['quantity'] for item in cart['items'])
    
    return render_template('cart.html', cart=cart, total_price=total_price, user=current_user.username)

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Cart WHERE user_id = %s", (current_user.id,))
    cart = cursor.fetchone()
    
    if not cart:
        cursor.execute("INSERT INTO Cart (user_id) VALUES (%s)", (current_user.id,))
        connection.commit()
        cart_id = cursor.lastrowid
    else:
        cart_id = cart['id']

    cursor.execute("SELECT * FROM CartItem WHERE cart_id = %s AND product_id = %s", (cart_id, product_id))
    cart_item = cursor.fetchone()
    
    if cart_item:
        cursor.execute("UPDATE CartItem SET quantity = quantity + 1 WHERE id = %s", (cart_item['id'],))
    else:
        cursor.execute("INSERT INTO CartItem (cart_id, product_id, quantity) VALUES (%s, %s, %s)", (cart_id, product_id, 1))

    connection.commit()
    cursor.close()
    connection.close()
    flash('Товар добавлен в корзину.')
    return redirect(url_for('main.index'))

@bp.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Cart WHERE user_id = %s", (current_user.id,))
    cart = cursor.fetchone()
    
    if not cart:
        flash('Корзина не найдена.', 'danger')
        return redirect(url_for('main.cart'))

    cursor.execute("SELECT * FROM CartItem WHERE cart_id = %s AND product_id = %s", (cart['id'], product_id))
    item = cursor.fetchone()
    
    if item:
        cursor.execute("DELETE FROM CartItem WHERE id = %s", (item['id'],))
        connection.commit()
        flash('Товар удален из корзины.', 'success')
    else:
        flash('Товар не найден в корзине.', 'danger')

    cursor.close()
    connection.close()
    return redirect(url_for('main.cart'))

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def moder_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.role != 'moderator' and current_user.role != 'admin'):
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Cart WHERE user_id = %s", (current_user.id,))
    cart = cursor.fetchone()
    
    if not cart or not cart['items']:
        flash('Ваша корзина пуста.', 'danger')
        return redirect(url_for('main.cart'))

    # Создание нового заказа
    cursor.execute("INSERT INTO Purchase (user_id, status) VALUES (%s, %s) RETURNING id", (current_user.id, 'pending'))
    purchase_id = cursor.fetchone()['id']
    
    # Добавление элементов заказа
    for item in cart['items']:
        cursor.execute("INSERT INTO PurchaseItem (purchase_id, product_id, quantity, cart_id) VALUES (%s, %s, %s, %s)", 
                       (purchase_id, item['product_id'], item['quantity'], cart['id']))

    # Очистка корзины
    cursor.execute("DELETE FROM Cart WHERE id = %s", (cart['id'],))

    connection.commit()
    cursor.close()
    connection.close()

    flash('Заказ успешно оформлен.', 'success')
    return redirect(url_for('main.index'))

# Административная панель - основная страница
@bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('admin_panel.html', users=users, products=products, categories=categories, admin=current_user.username)

@bp.route('/moderator')
@login_required
@moder_required
def moderator():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('moderator.html', products=products, categories=categories, moder=current_user.username)

@bp.route('/admin/change_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def change_role(user_id):
    if not current_user.role == 'admin':
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('Пользователь не найден.', 'danger')
        cursor.close()
        connection.close()
        return redirect(url_for('main.admin_panel'))

    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role in ['user', 'moderator', 'admin']:
            cursor.execute("UPDATE User SET role = %s WHERE id = %s", (new_role, user_id))
            connection.commit()
            flash(f'Роль пользователя {user["username"]} успешно изменена на {new_role}.', 'success')
        else:
            flash('Недопустимая роль.', 'danger')

        cursor.close()
        connection.close()
        return redirect(url_for('main.admin_panel'))

    cursor.close()
    connection.close()
    return render_template('change_role.html', user=user)


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.role == 'admin':
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute("DELETE FROM User WHERE id = %s", (user_id,))
        connection.commit()
        flash(f'Пользователь {user["username"]} был успешно удален.', 'success')
    else:
        flash('Пользователь не найден.', 'danger')

    cursor.close()
    connection.close()
    return redirect(url_for('admin'))


@bp.route('/admin/product/create', methods=['GET', 'POST'])
@login_required
@moder_required
def create_product():
    form = ProductForm()
    if request.method == 'POST':
        name = form.name.data
        description = form.description.data
        price = form.price.data
        image = form.image.data
        category_id = form.category_id.data

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Product (name, description, price, image_path, category_id) VALUES (%s, %s, %s, %s, %s)",
                       (name, description, price, image, category_id))
        connection.commit()
        flash('Товар успешно создан.')

        cursor.close()
        connection.close()
        return redirect(url_for('main.admin_panel' if current_user.role == 'admin' else 'main.moderator'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('create_product.html', categories=categories)


# Редактирование товара
@bp.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@moder_required
def edit_product(product_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    form = ProductForm()
    if request.method == 'POST':
        name = form.name.data
        description = form.description.data
        price = form.price.data
        image_path = form.image.data
        category_id = form.category_id.data

        cursor.execute("""
            UPDATE Product 
            SET name = %s, description = %s, price = %s, image_path = %s, category_id = %s 
            WHERE id = %s
        """, (name, description, price, image_path, category_id, product_id))
        connection.commit()
        flash('Товар успешно обновлен.')

        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    cursor.execute("SELECT * FROM Product WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('edit_product.html', product=product, categories=categories)

# Удаление товара
@bp.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
@moder_required
def delete_product(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM Product WHERE id = %s", (product_id,))
    connection.commit()
    flash('Товар удален.')

    cursor.close()
    connection.close()

    if current_user.role == 'admin':
        return redirect(url_for('main.admin_panel'))
    if current_user.role == 'moderator':
        return redirect(url_for('main.moderator'))

# Создание категории
@bp.route('/admin/category/create', methods=['GET', 'POST'])
@login_required
@moder_required
def create_category():
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        cursor.execute("INSERT INTO Category (name) VALUES (%s)", (name,))
        connection.commit()
        flash('Категория успешно создана.')

        cursor.close()
        connection.close()

        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    cursor.close()
    connection.close()
    return render_template('create_category.html')

# Редактирование категории
@bp.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@moder_required
def edit_category(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        cursor.execute("UPDATE Category SET name = %s WHERE id = %s", (name, category_id))
        connection.commit()
        flash('Категория успешно обновлена.')

        cursor.close()
        connection.close()

        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    cursor.execute("SELECT * FROM Category WHERE id = %s", (category_id,))
    category = cursor.fetchone()

    cursor.close()
    connection.close()
    return render_template('edit_category.html', category=category)

# Удаление категории
@bp.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@login_required
@moder_required
def delete_category(category_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Category WHERE id = %s", (category_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Категория удалена.')
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_panel'))
    if current_user.role == 'moderator':
        return redirect(url_for('main.moderator'))

@bp.route('/orders')
@login_required
@moder_required
def orders():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Purchase")
    purchases = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('orders.html', purchases=purchases)

@bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@moder_required
@login_required
def update_order_status(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Purchase WHERE id = %s", (order_id,))
    purchase = cursor.fetchone()
    
    if not purchase:
        flash('Заказ не найден.', 'danger')
        cursor.close()
        connection.close()
        return redirect(url_for('main.orders'))

    new_status = request.form.get('status')
    cursor.execute("UPDATE Purchase SET status = %s WHERE id = %s", (new_status, order_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash(f'Статус заказа {order_id} успешно изменен на {new_status}.', 'success')
    return redirect(url_for('main.orders'))