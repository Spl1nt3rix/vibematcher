# app/auth/__init__.py — создание Blueprint'а для модуля авторизации
from flask import Blueprint

# Создаём Blueprint с именем 'auth'. К нему будут привязаны маршруты в routes.py
bp = Blueprint('auth', __name__)

# Импортируем маршруты, чтобы они зарегистрировались в Blueprint'е
from app.auth import routes