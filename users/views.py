# views.py
from .models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from datetime import datetime
# Получение коллекции пользователей
users_collection = settings.MONGO_DB['users']
@csrf_exempt
def create_user(request):
    """
    Создание нового пользователя. Если пользователь с таким username или telegram_id уже существует, возвращаем ошибку.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Проверка на существование пользователя по username или telegram_id
            if users_collection.find_one({"$or": [{"username": data.get("username")}, {"telegram_id": data.get("telegram_id")}]}) is not None:
                return JsonResponse({"status": "error", "message": "Пользователь с таким username или telegram_id уже существует."}, status=400)

            # Подготовка данных нового пользователя
                # Создание объекта User
                new_user = User(
                    username=data.get("username"),
                    age=data.get("age", 0),
                    avatar=data.get("avatar"),
                    balance=data.get("balance", 0.0),
                    is_premium=data.get("is_premium", False),
                    last_seen=datetime.now(),  # Устанавливаем текущее время
                    reference=data.get("reference"),
                    streak=data.get("streak"),
                    telegram_id=data.get("telegram_id"),
                    top_group=data.get("top_group", 0),
                    top_percent=data.get("top_percent", 0),
                    wallet=data.get("wallet")
                )

            # Вставка нового пользователя в коллекцию
            users_collection.insert_one(new_user.__dict__)

            return JsonResponse({"status": "success", "message": "Пользователь успешно создан."}, status=201)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Недопустимый метод запроса."}, status=400)


@csrf_exempt
def get_users(request):
    """
    Получение списка всех пользователей.
    """
    if request.method == 'GET':
        try:
            # Поиск всех пользователей без поля _id
            users = list(users_collection.find({}, {"_id": 0}))
            return JsonResponse({"status": "success", "users": users}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Недопустимый метод запроса."}, status=400)