# Импортируем библиотеку os для работы с путями операционной системы
import os
# Импортируем load_dotenv для чтения секретных ключей из файла .env (если он есть)
from dotenv import load_dotenv

# Определяем базовый путь — папка, в которой лежит этот файл config.py
basedir = os.path.abspath(os.path.dirname(__file__))
# Загружаем переменные из .env (например, секретный ключ, настройки БД)
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """
    Класс настроек нашего Flask-приложения.
    Все параметры, используемые приложением, собраны здесь.
    """

    # Секретный ключ нужен для безопасности: подписи сессий, токенов.
    # Если в переменных окружения есть SECRET_KEY, берём его; иначе значение по умолчанию.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Строка подключения к базе данных.
    # Если указана переменная окружения DATABASE_URL (например, на сервере), используем её.
    # Иначе используем SQLite — простой файл базы данных в папке проекта.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

    # Отключаем функцию, которая посылает сигналы при каждом изменении в БД (экономит память).
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Папка, куда будут загружаться аватарки пользователей.
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')

    # Максимальный размер загружаемого файла: 16 мегабайт.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # API-ключ для Google Vision (если захотим подключить полноценную ИИ-модерацию).
    GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY')

    # Флаг: использовать ли настоящую ИИ-модерацию или заглушку.
    # Берём из переменных окружения; по умолчанию False (заглушка).
    USE_AI_MODERATION = os.environ.get('USE_AI_MODERATION', 'False') == 'True'