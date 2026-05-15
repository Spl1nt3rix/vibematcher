# app/models.py — здесь описаны все таблицы базы данных (модели)
from datetime import datetime
from flask_login import UserMixin  # даёт стандартные методы для Flask-Login
from werkzeug.security import generate_password_hash, check_password_hash  # хэширование паролей
from app import db, login_manager


class User(UserMixin, db.Model):
    """
    Модель пользователя.
    Наследуемся от UserMixin, чтобы работала авторизация через Flask-Login.
    """
    # Поле id — первичный ключ, целое число, генерируется автоматически
    id = db.Column(db.Integer, primary_key=True)
    # Имя пользователя, уникальное, индексируемое для быстрого поиска
    username = db.Column(db.String(64), index=True, unique=True)
    # Email, тоже уникальный
    email = db.Column(db.String(120), index=True, unique=True)
    # Хэш пароля (не сам пароль!)
    password_hash = db.Column(db.String(128))
    # Дата регистрации, ставится автоматически
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Время последней активности (онлайн-статус)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Активен ли аккаунт (можем заморозить пользователя)
    is_active = db.Column(db.Boolean, default=True)

    # Связь с профилем: у одного пользователя один профиль
    # uselist=False означает «один к одному»
    # cascade='all, delete-orphan' — при удалении пользователя удаляется и профиль
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')

    # Связи с таблицей заявок (Match): исходящие и входящие
    # foreign_keys уточняет, какой столбец используется для связи
    sent_matches = db.relationship('Match', foreign_keys='Match.user_id',
                                   backref='sender', lazy='dynamic')
    received_matches = db.relationship('Match', foreign_keys='Match.target_id',
                                       backref='receiver', lazy='dynamic')

    # Связи с чёрным списком: кого заблокировал пользователь и кто заблокировал его
    blocked_users = db.relationship('BlockedUser', foreign_keys='BlockedUser.user_id',
                                    backref='blocker', lazy='dynamic')
    blocked_by = db.relationship('BlockedUser', foreign_keys='BlockedUser.blocked_id',
                                 backref='blocked_user', lazy='dynamic')

    def set_password(self, password):
        """Устанавливает хэш пароля."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет, соответствует ли введённый пароль хэшу."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_online(self):
        """Свойство: True, если пользователь был активен в последние 10 минут."""
        if self.last_seen:
            from datetime import timedelta
            return datetime.utcnow() - self.last_seen < timedelta(minutes=10)
        return False

    def __repr__(self):
        """Как объект будет выглядеть при выводе в консоли."""
        return f'<User {self.username}>'


# Загрузчик пользователя, нужен Flask-Login для восстановления объекта пользователя по его ID
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Profile(db.Model):
    """Профиль пользователя — дополнительная информация."""
    id = db.Column(db.Integer, primary_key=True)
    # Ключ на таблицу user, уникальный (один профиль на одного пользователя)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    birth_date = db.Column(db.Date)  # дата рождения
    gender = db.Column(db.String(10))  # 'male', 'female', 'other'
    city = db.Column(db.String(100))
    about_me = db.Column(db.Text)  # описание «О себе»
    interests = db.Column(db.Text)  # интересы через запятую
    hair_color = db.Column(db.String(30))
    nationality = db.Column(db.String(50))
    avatar = db.Column(db.String(200), default='default.jpg')  # имя файла аватара
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    is_visible = db.Column(db.Boolean, default=True)
    # Теги, полученные ИИ по фото (в виде JSON-строки)
    photo_tags = db.Column(db.Text)

    def age(self):
        """Вычисляет возраст на основе даты рождения."""
        if self.birth_date:
            today = datetime.utcnow().date()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def get_tags_list(self):
        """Возвращает теги в виде списка Python из JSON-строки."""
        if self.photo_tags:
            import json
            return json.loads(self.photo_tags)
        return []


class Photo(db.Model):
    """Дополнительные фотографии (пока не используются, но могут пригодиться)."""
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    filename = db.Column(db.String(200))
    is_avatar = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Match(db.Model):
    """Заявка (отклик) от одного пользователя другому."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # кто отправил
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # кому отправили
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ограничение: нельзя отправить заявку одному и тому же человеку дважды
    __table_args__ = (db.UniqueConstraint('user_id', 'target_id', name='unique_match'),)


class BlockedUser(db.Model):
    """Чёрный список — связь «кто» и «кого» заблокировал."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'blocked_id', name='unique_block'),)


class BlacklistWord(db.Model):
    """Таблица запрещённых слов (для текстового фильтра)."""
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True)