# app/api/__init__.py — Blueprint для API-методов (AJAX-запросы)
from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes