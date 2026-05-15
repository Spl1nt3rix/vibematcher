# app/auth/routes.py — маршруты, связанные с регистрацией и входом
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp  # импортируем Blueprint, к которому будем привязываться
from app.models import User, Profile
from app.forms import RegistrationForm, LoginForm


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации.
    GET — показываем форму, POST — обрабатываем данные.
    """
    # Если пользователь уже авторизован, нельзя регистрироваться — перекидываем на главную
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    # Если метод POST и данные формы валидны (прошли проверки)
    if form.validate_on_submit():
        # Создаём нового пользователя
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)  # пароль хэшируется внутри метода
        db.session.add(user)
        db.session.commit()
        # Сразу создаём пустой профиль
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        flash('Поздравляем, вы зарегистрированы! Теперь войдите.', 'success')
        return redirect(url_for('auth.login'))
    # Если GET (или ошибки в форме), показываем html-шаблон с формой
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Ищем пользователя по введённому логину
        user = User.query.filter_by(username=form.username.data).first()
        # Проверяем, существует ли пользователь и совпадает ли пароль
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль', 'danger')
            return redirect(url_for('auth.login'))
        # Авторизуем пользователя (создаём сессию)
        login_user(user, remember=form.remember_me.data)
        # Обновляем время последнего захода
        user.last_seen = datetime.utcnow()
        db.session.commit()
        # Если пользователь пытался зайти на какую-то страницу, его перебросит туда,
        # иначе — на главную
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
    """Выход из учётной записи."""
    logout_user()
    return redirect(url_for('main.index'))