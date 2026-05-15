# app/main/routes.py — основные страницы приложения: поиск, профиль, заявки и т.д.
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
import os
import json
from app import db
from app.main import bp
from app.forms import EditProfileForm, SearchForm
from app.models import User, Profile, Photo, Match, BlockedUser, BlacklistWord
from app.utils.image_moderation import moderate_image, get_image_tags
from werkzeug.utils import secure_filename


# Хук before_request выполняется перед каждым запросом
@bp.before_request
def update_last_seen():
    """Обновляем время последней активности пользователя."""
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
def index():
    """Главная страница (лендинг). Если пользователь уже вошёл — перенаправляем в поиск."""
    if current_user.is_authenticated:
        return redirect(url_for('main.search'))
    return render_template('index.html')


@bp.route('/profile/<username>')
@login_required
def profile(username):
    """Просмотр профиля другого пользователя по его username."""
    user = User.query.filter_by(username=username).first_or_404()
    # Проверяем, не заблокирован ли текущий пользователь этим человеком
    if BlockedUser.query.filter_by(user_id=user.id, blocked_id=current_user.id).first():
        flash('Вы не можете просматривать этот профиль.', 'warning')
        return redirect(url_for('main.search'))
    # Проверяем статус матча: если принят, показываем контакты
    match = Match.query.filter(
        ((Match.user_id == current_user.id) & (Match.target_id == user.id)) |
        ((Match.user_id == user.id) & (Match.target_id == current_user.id))
    ).first()
    show_contacts = match and match.status == 'accepted'
    return render_template('profile.html', user=user, show_contacts=show_contacts)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование собственного профиля."""
    form = EditProfileForm(obj=current_user.profile)
    if form.validate_on_submit():
        profile = current_user.profile
        form.populate_obj(profile)  # переносим данные из формы в объект профиля
        # Проверяем описание на запрещённые слова
        if contains_blacklisted_words(profile.about_me):
            flash('Текст содержит запрещённые слова. Пожалуйста, измените описание.', 'danger')
            return render_template('edit_profile.html', form=form)
        db.session.commit()
        flash('Профиль обновлён.', 'success')
        return redirect(url_for('main.profile', username=current_user.username))
    return render_template('edit_profile.html', form=form)


@bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Загрузка аватарки."""
    if 'avatar' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('main.edit_profile'))
    file = request.files['avatar']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('main.edit_profile'))
    if file and allowed_file(file.filename):
        # Формируем безопасное имя файла
        filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}.jpg")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # ИИ-модерация (если включена) — проверяем, не содержит ли фото запрещённый контент
        if current_app.config['USE_AI_MODERATION']:
            if not moderate_image(filepath):
                os.remove(filepath)
                flash('Изображение не прошло модерацию (содержит неприемлемый контент).', 'danger')
                return redirect(url_for('main.edit_profile'))

        # Получаем теги от ИИ и сохраняем в профиле
        tags = get_image_tags(filepath)
        current_user.profile.photo_tags = json.dumps(tags)
        current_user.profile.avatar = filename
        db.session.commit()
        flash('Аватар обновлён.', 'success')
    return redirect(url_for('main.edit_profile'))


@bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Страница поиска людей."""
    form = SearchForm(request.args)  # позволяет работать через GET-параметры в URL
    # Базовый запрос: все пользователи, кроме себя
    query = User.query.join(Profile).filter(User.id != current_user.id)

    # Исключаем заблокированных (в обе стороны)
    blocked_ids = [b.blocked_id for b in current_user.blocked_users]
    blocker_ids = [b.user_id for b in current_user.blocked_by]
    excluded = blocked_ids + blocker_ids + [current_user.id]
    query = query.filter(~User.id.in_(excluded))

    # Применяем фильтры, если они указаны
    if form.gender.data:
        query = query.filter(Profile.gender == form.gender.data)
    if form.age_min.data:
        min_birth_date = datetime.utcnow().date() - timedelta(days=form.age_min.data * 365)
        query = query.filter(Profile.birth_date <= min_birth_date)
    if form.age_max.data:
        max_birth_date = datetime.utcnow().date() - timedelta(days=form.age_max.data * 365)
        query = query.filter(Profile.birth_date >= max_birth_date)
    if form.city.data:
        query = query.filter(Profile.city.ilike(f"%{form.city.data}%"))
    if form.hair_color.data:
        query = query.filter(Profile.hair_color.ilike(f"%{form.hair_color.data}%"))
    if form.nationality.data:
        query = query.filter(Profile.nationality.ilike(f"%{form.nationality.data}%"))
    if form.interests.data:
        # Поиск по каждому слову из запроса в интересах и описании
        keywords = form.interests.data.split()
        for kw in keywords:
            query = query.filter(Profile.interests.ilike(f"%{kw}%") | Profile.about_me.ilike(f"%{kw}%"))
    if form.online_only.data:
        # Пользователи, заходившие в последние 10 минут
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
        query = query.filter(User.last_seen >= ten_minutes_ago)

    users = query.all()
    return render_template('search.html', form=form, users=users)


@bp.route('/send_match/<int:user_id>', methods=['POST'])
@login_required
def send_match(user_id):
    """Отправить заявку-отклик другому пользователю."""
    target = User.query.get_or_404(user_id)
    # Не даём отправить заявку, если он вас заблокировал
    if BlockedUser.query.filter_by(user_id=target.id, blocked_id=current_user.id).first():
        flash('Невозможно отправить заявку.', 'danger')
        return redirect(url_for('main.search'))
    existing = Match.query.filter_by(user_id=current_user.id, target_id=target.id).first()
    if existing:
        flash('Вы уже отправляли заявку этому пользователю.', 'info')
    else:
        match = Match(user_id=current_user.id, target_id=target.id)
        db.session.add(match)
        db.session.commit()
        flash('Заявка отправлена!', 'success')
    return redirect(url_for('main.profile', username=target.username))


@bp.route('/matches')
@login_required
def matches():
    """Страница с входящими, исходящими и взаимными заявками."""
    received = Match.query.filter_by(target_id=current_user.id, status='pending').all()
    sent = Match.query.filter_by(user_id=current_user.id, status='pending').all()
    accepted = Match.query.filter(
        ((Match.user_id == current_user.id) | (Match.target_id == current_user.id)),
        Match.status == 'accepted'
    ).all()
    return render_template('matches.html', received=received, sent=sent, accepted=accepted)


@bp.route('/accept_match/<int:match_id>', methods=['POST'])
@login_required
def accept_match(match_id):
    """Принять входящую заявку."""
    match = Match.query.get_or_404(match_id)
    if match.target_id != current_user.id:
        abort(403)  # доступ запрещён, если это не ваша заявка
    match.status = 'accepted'
    db.session.commit()
    flash('Вы приняли заявку! Теперь контакты видны обоим.', 'success')
    return redirect(url_for('main.matches'))


@bp.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    """Заблокировать пользователя."""
    if current_user.id == user_id:
        flash('Нельзя заблокировать самого себя.', 'danger')
        return redirect(url_for('main.search'))
    blocked = BlockedUser.query.filter_by(user_id=current_user.id, blocked_id=user_id).first()
    if not blocked:
        block = BlockedUser(user_id=current_user.id, blocked_id=user_id)
        db.session.add(block)
        db.session.commit()
        flash('Пользователь добавлен в чёрный список.', 'info')
    return redirect(request.referrer or url_for('main.search'))


@bp.route('/blocked')
@login_required
def blocked_list():
    """Просмотр чёрного списка."""
    blocks = current_user.blocked_users.all()
    return render_template('blocked.html', blocks=blocks)


@bp.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    """Убрать пользователя из чёрного списка."""
    block = BlockedUser.query.filter_by(user_id=current_user.id, blocked_id=user_id).first()
    if block:
        db.session.delete(block)
        db.session.commit()
        flash('Пользователь разблокирован.', 'success')
    else:
        flash('Пользователь не найден в чёрном списке.', 'warning')
    return redirect(url_for('main.blocked_list'))


# Вспомогательные функции (не являются маршрутами)
def contains_blacklisted_words(text):
    """Проверяет, есть ли в тексте слова из таблицы blacklist_word."""
    if not text:
        return False
    words = BlacklistWord.query.all()
    for w in words:
        if w.word.lower() in text.lower():
            return True
    return False


def allowed_file(filename):
    """Проверяет, допустимое ли расширение у файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}