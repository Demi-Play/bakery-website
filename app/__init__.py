from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()  # Инициализация LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supedawrseddacreweqtkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bakery.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Настройка сообщения для неавторизованных пользователей
    login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
    login_manager.login_message_category = "warning"

    # Импорт моделей после инициализации базы данных и приложения
    from .models import User, Product, Category

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Регистрация маршрутов
    from . import routes
    app.register_blueprint(routes.bp)

    return app
