# app/api/routes.py — API-маршруты (отвечают в формате JSON, без перезагрузки страницы)
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Match


@bp.route('/like/<int:user_id>', methods=['POST'])
@login_required
def like(user_id):
    """
    Поставить лайк (отклик) через API.
    Возвращает JSON с результатом.
    """
    match = Match.query.filter_by(user_id=current_user.id, target_id=user_id).first()
    if match:
        return jsonify({'status': 'error', 'message': 'Уже есть лайк'}), 400
    match = Match(user_id=current_user.id, target_id=user_id)
    db.session.add(match)
    db.session.commit()
    return jsonify({'status': 'success'})


@bp.route('/online_status')
@login_required
def online_status():
    """Возвращает время последней активности текущего пользователя."""
    return jsonify({'last_seen': current_user.last_seen.isoformat()})