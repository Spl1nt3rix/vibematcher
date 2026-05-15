# seed.py — скрипт для создания тестовых данных в базе
# Импортируем create_app и объект db (базу данных) из пакета app
from app import create_app, db
# Импортируем модели (таблицы), с которыми будем работать
from app.models import User, Profile
# Импортируем date для указания даты рождения
from datetime import date

# Создаём приложение Flask
app = create_app()

# Указываем, что весь код внутри блока with выполняется в контексте приложения
# Это нужно, потому что Flask-расширения требуют активного приложения
with app.app_context():
    # Удаляем все таблицы, если они уже были, и создаём новые (чистая база)
    db.drop_all()
    db.create_all()
    print("Таблицы созданы заново.")

    # Создаём первого тестового пользователя
    u1 = User(username='alice', email='alice@test.com')
    u1.set_password('123')  # задаём пароль (он будет хэширован)
    db.session.add(u1)
    db.session.commit()  # сохраняем, чтобы получить идентификатор user.id

    # Создаём профиль для первого пользователя
    p1 = Profile(
        user_id=u1.id,
        first_name='Алиса',
        birth_date=date(1995, 5, 15),
        gender='female',
        city='Москва',
        about_me='Люблю музыку и прогулки',
        interests='музыка, кино, спорт',
        hair_color='блонд',
        nationality='русская'
    )
    db.session.add(p1)

    # Создаём второго тестового пользователя
    u2 = User(username='bob', email='bob@test.com')
    u2.set_password('123')
    db.session.add(u2)
    db.session.commit()

    # Создаём профиль для второго пользователя
    p2 = Profile(
        user_id=u2.id,
        first_name='Боб',
        birth_date=date(1993, 10, 22),
        gender='male',
        city='Санкт-Петербург',
        about_me='Программист, ищу музу',
        interests='программирование, игры',
        hair_color='чёрный',
        nationality='русский'
    )
    db.session.add(p2)

    # Применяем все добавленные объекты к базе
    db.session.commit()
    print("Тестовые пользователи alice и bob созданы (пароль: 123).")