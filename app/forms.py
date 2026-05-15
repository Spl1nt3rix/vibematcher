# app/forms.py — здесь мы описываем веб-формы с помощью Flask-WTF
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from app.models import User


class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя."""
    username = StringField('Логин', validators=[DataRequired(message='Поле обязательно'),
                                                Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(message='Неверный формат email')])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль',
                              validators=[DataRequired(),
                                          EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')

    # Кастомные валидаторы: проверяем уникальность логина и email в базе
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот логин уже занят.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже используется.')


class LoginForm(FlaskForm):
    """Форма входа."""
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class EditProfileForm(FlaskForm):
    """Форма редактирования своего профиля."""
    first_name = StringField('Имя', validators=[Length(max=64)])
    last_name = StringField('Фамилия', validators=[Length(max=64)])
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Пол', choices=[('', 'Не указано'), ('male', 'Мужской'),
                                         ('female', 'Женский'), ('other', 'Другой')])
    city = StringField('Город', validators=[Length(max=100)])
    about_me = TextAreaField('О себе', validators=[Length(max=500)])
    interests = StringField('Интересы (через запятую)', validators=[Length(max=200)])
    hair_color = StringField('Цвет волос')
    nationality = StringField('Национальность')
    contact_phone = StringField('Телефон (будет виден только после взаимного матча)')
    contact_email = StringField('Email для контактов')
    submit = SubmitField('Сохранить')


class SearchForm(FlaskForm):
    """Форма поиска людей."""
    gender = SelectField('Пол', choices=[('', 'Любой'), ('male', 'Мужской'),
                                         ('female', 'Женский')])
    age_min = IntegerField('Возраст от', validators=[Optional()])
    age_max = IntegerField('Возраст до', validators=[Optional()])
    city = StringField('Город')
    hair_color = StringField('Цвет волос')
    nationality = StringField('Национальность')
    interests = StringField('Интересы (поиск по вайбу)')
    online_only = BooleanField('Только онлайн')
    submit = SubmitField('Искать')