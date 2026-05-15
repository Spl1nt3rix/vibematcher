# app/utils/image_moderation.py — утилиты для работы с ИИ (проверка фото, получение тегов)
import os
import json
from flask import current_app


def moderate_image(filepath):
    """
    Проверяет, является ли изображение приемлемым.
    Если USE_AI_MODERATION=True, должен обращаться к Google Vision API.
    В данный момент — заглушка, всегда возвращает True.
    """
    if current_app.config['USE_AI_MODERATION']:
        # Настоящий код запроса к API был бы здесь
        return True
    else:
        # Заглушка: считаем, что все фото проходят
        return True


def get_image_tags(filepath):
    """
    Получает список меток (тегов) для фотографии, например ['очки', 'блондин'].
    При включённом ИИ здесь должен быть запрос к Vision API, сейчас — пустой список.
    """
    if current_app.config['USE_AI_MODERATION']:
        # Здесь был бы запрос к API и возврат меток
        return []
    else:
        return []