from flask import Flask
from flask_login import LoginManager
import os
import mysql.connector

login_manager = LoginManager()  # Инициализация LoginManager

def get_db_connection():
        return mysql.connector.connect(
            host='sql.freedb.tech',
            user=os.environ.get('DB_USER', 'freedb_d33mm11'),
            password=os.environ.get('DB_PASSWORD', 'TaTp%PDSNE5ZEFd'),
            database=os.environ.get('DB_NAME', 'freedb_bakery')
        )

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supedawrseddacreweqtkey'

    # Создайте подключение к MySQL базе данных
    

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Настройка сообщения для неавторизованных пользователей
    login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
    login_manager.login_message_category = "warning"

    # Импорт моделей после инициализации базы данных и приложения

    @login_manager.user_loader
    def load_user(user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user_data:
            return user_data  # Предполагается, что User принимает данные в конструкторе
        return None


    # Регистрация маршрутов
    from . import routes
    app.register_blueprint(routes.bp)


    return app
