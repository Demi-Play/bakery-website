from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Product, Category, Cart, CartItem, Purchase, PurchaseItem
from .forms import RegisterForm, LoginForm, ProductForm

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search', '')
    sort_option = request.form.get('sort', 'name')

    products = Product.query.all()

    if search_query:
        products = [product for product in products if search_query.lower() in product.name.lower()]
    
    products.sort(key=lambda x: getattr(x, sort_option))
    
    return render_template('index.html', products=products)

@bp.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search', '')
    sort_option = request.form.get('sort', 'name')
    
    products = Product.query.all()
    
    if search_query:
        products = [product for product in products if search_query.lower() in product.name.lower()]
    
    products.sort(key=lambda x: getattr(x, sort_option))

    return render_template('index.html', products=products)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при записи в БД: {e}")

        flash('Регистрация успешна. Войдите в свою учетную запись.')
        return redirect(url_for('main.login'))
    else:
        print(form.errors)

    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_successful = login_user(user)
            if login_successful:
                flash('Вы успешно вошли в систему.', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Ошибка авторизации.', 'danger')
                return redirect(url_for('main.cart'))
        else:
            flash('Неправильное имя пользователя или пароль.', 'danger')
    return render_template('login.html', form=form)



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@bp.route('/cart')
@login_required
def cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart and cart.items:
        total_price = sum(item.product.price * item.quantity for item in cart.items)
    else:
        total_price = 0.0
    return render_template('cart.html', cart=cart, total_price=total_price, user=current_user.username)


@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash('Товар добавлен в корзину.')
    return redirect(url_for('main.index'))

@bp.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('Корзина не найдена.', 'danger')
        return redirect(url_for('main.cart'))

    # Поиск товара в корзине
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Товар удален из корзины.', 'success')
    else:
        flash('Товар не найден в корзине.', 'danger')

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
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash('Ваша корзина пуста.', 'danger')
        return redirect(url_for('main.cart'))

    # Создание нового заказа
    purchase = Purchase(user_id=current_user.id, status='pending')
    db.session.add(purchase)
    db.session.commit()  # Сохраняем заказ, чтобы получить его id
    
    # Добавление элементов заказа
    for item in cart.items:
        purchase_item = PurchaseItem(purchase_id=purchase.id, product_id=item.product.id, quantity=item.quantity, cart_id=cart.id)  # Передаем cart_id
        db.session.add(purchase_item)

    # Сохранение всех изменений в базе данных
    db.session.commit()

    # Очистка корзины
    db.session.delete(cart)
    db.session.commit()

    flash('Заказ успешно оформлен.', 'success')
    return redirect(url_for('main.index'))




# Административная панель - основная страница
@bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin_panel.html', users=users, products=products, categories=categories, admin=current_user.username)

@bp.route('/moderator')
@login_required
@moder_required
def moderator():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('moderator.html', products=products, categories=categories, moder=current_user.username)


@bp.route('/admin/change_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def change_role(user_id):
    if not current_user.role == 'admin':
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('main.admin_panel'))

    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role in ['user', 'moderator', 'admin']:
            user.role = new_role
            db.session.commit()
            flash(f'Роль пользователя {user.username} успешно изменена на {new_role}.', 'success')
        else:
            flash('Недопустимая роль.', 'danger')

        return redirect(url_for('main.admin_panel'))

    return render_template('change_role.html', user=user)


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.role == 'admin':
        flash('У вас нет прав для выполнения этого действия.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.username} был успешно удален.', 'success')
    else:
        flash('Пользователь не найден.', 'danger')

    return redirect(url_for('admin'))

# import shutil
# import os

# Создание товара
@bp.route('/admin/product/create', methods=['GET', 'POST'])
@login_required
@moder_required
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = form.price.data
        image = form.image.data
        category_id = request.form.get('category_id')

        # Сохранение изображения
        # if image:
        #     image_filename = os.path.basename(image)
        #     image_path = os.path.join('media', image_filename)
        #     shutil.copy(image, image_path)
        #     image_db_path = os.path.join('media', image_filename)  # Путь для базы данных

        product = Product(name=name, description=description, price=price, image_path=image, category_id=category_id)
        db.session.add(product)
        db.session.commit()
        flash('Товар успешно создан.')
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    categories = Category.query.all()
    return render_template('create_product.html', form=form, categories=categories)


# Редактирование товара
@bp.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@moder_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.image_path = form.image.data
        product.category_id = request.form.get('category_id')

        # # Сохранение изображения
        # if product.image:
        #     image_filename = os.path.basename(product.image)
        #     image_path = os.path.join('media', image_filename)
        #     shutil.copy(product.image, image_path)
        #     image_db_path = os.path.join('media', image_filename)  # Путь для базы данных
        # product.image = image_db_path

        db.session.commit()
        flash('Товар успешно обновлен.')
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    categories = Category.query.all()
    return render_template('edit_product.html', form=form, product=product, categories=categories)

# Удаление товара
@bp.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@login_required
@moder_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удален.')
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_panel'))
    if current_user.role == 'moderator':
        return redirect(url_for('main.moderator'))

# Создание категории
@bp.route('/admin/category/create', methods=['GET', 'POST'])
@login_required
@moder_required
def create_category():
    if request.method == 'POST':
        name = request.form['name']
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash('Категория успешно создана.')
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    return render_template('create_category.html')

# Редактирование категории
@bp.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@moder_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        flash('Категория успешно обновлена.')
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        if current_user.role == 'moderator':
            return redirect(url_for('main.moderator'))

    return render_template('edit_category.html', category=category)

# Удаление категории
@bp.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@login_required
@moder_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена.')
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_panel'))
    if current_user.role == 'moderator':
        return redirect(url_for('main.moderator'))
    

@bp.route('/orders')
@login_required
@moder_required
def orders():
    purchases = Purchase.query.all()  # Получаем все заказы
    return render_template('orders.html', purchases=purchases)

@bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@moder_required
@login_required
def update_order_status(order_id):
    purchase = Purchase.query.get(order_id)
    if not purchase:
        flash('Заказ не найден.', 'danger')
        return redirect(url_for('main.orders'))

    new_status = request.form.get('status')
    purchase.status = new_status
    db.session.commit()
    flash(f'Статус заказа {order_id} успешно изменен на {new_status}.', 'success')

    return redirect(url_for('main.orders'))