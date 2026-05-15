# wsgi.py — запуск production-сервера Waitress (быстрее, стабильнее, для реального использования)
import sys
from app import create_app
from waitress import serve

# Оборачиваем создание приложения в try, чтобы увидеть ошибки
try:
    app = create_app()
    print("Запуск Waitress на http://0.0.0.0:8080...")
    # Запускаем Waitress на порту 8080 с 8 потоками
    serve(app, host='0.0.0.0', port=8080, threads=8)
except Exception as e:
    # Если что-то пошло не так, выводим traceback в консоль и завершаем работу
    print("Ошибка при запуске:", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)