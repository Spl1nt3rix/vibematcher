# app/__init__.py — инициализация пакета app и создание объекта Flask-приложения
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config  # наши настройки из config.py

# Создаём глобальные объекты расширений (пока без приложения)
db = SQLAlchemy()  # для работы с базой данных
login_manager = LoginManager()  # для авторизации пользователей
# Указываем, на какую страницу перенаправлять, если пользователь не авторизован
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'


def create_app(config_class=Config):
    """
    Фабрика приложений — функция, которая собирает всё воедино.
    Принимает класс конфигурации (по умолчанию Config).
    """
    app = Flask(__name__)  # создаём экземпляр Flask
    app.config.from_object(config_class)  # загружаем настройки из класса Config

    # Инициализируем расширения, привязывая их к нашему приложению
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)  # для удобного обновления структуры БД при изменениях моделей

    # Регистрируем Blueprint'ы (отдельные модули с маршрутами)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')  # все маршруты auth будут с префиксом /auth

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)  # основные маршруты без префикса

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')  # API-маршруты с префиксом /api

    # Создаём папку для загрузок, если её ещё нет
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Обработчик ошибки 404 (страница не найдена)
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    return app