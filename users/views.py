from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from datetime import datetime
from .models import LeaderboardEntry
from pymongo import ReturnDocument
from pymongo import DESCENDING
from bson import ObjectId
# Получение коллекции пользователей
users_collection = settings.MONGO_DB['users']
rewards_collection = settings.MONGO_DB['rewards']
frens_collection = settings.MONGO_DB['frens']
tasks_collection = settings.MONGO_DB['tasks']
leaderboard_collection = settings.MONGO_DB['leaderboard']
@csrf_exempt
def create_user(request):
    """
    Создание нового пользователя. Если пользователь с таким username или telegram_id уже существует, возвращаем ошибку.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get("username")
            telegram_id = data.get("telegram_id")
            age = data.get("age", 0)

            # Проверка на существование пользователя
            existing_user = users_collection.find_one({"telegram_id": telegram_id})
            if existing_user:
                return JsonResponse({"status": "error", "message": "User already exists"}, status=400)

            # Создание объекта User
            new_user = {
                "username": username,
                "telegram_id": telegram_id,
                "age": age,
                "avatar": None,
                "balance": 0.0,
                "is_premium": data.get("is_premium", False),
                "last_seen": datetime.now(),
                "reference": data.get("reference", None),
                "streak": None,
                "top_group": 0,
                "top_percent": 0,
                "wallet": None
            }

            # Вставка нового пользователя в коллекцию
            users_collection.insert_one(new_user)

            rewards_collection.insert_one({
                "telegram_id": telegram_id,
                "age": age,
                "boost": 0,
                "game": 0.0,
                "daily": 0.0,
                "frens": 0.0,
                "premium": 0,
                "tasks": 0,
                "total": 0.0
            })
            frens_collection.insert_one({"telegram_id": telegram_id, "count": 0, "frens": []})

            tasks_collection.insert_one({
                "telegram_id": telegram_id,
                "tasks": [
                    {"id": 1, "complete": False},
                    {"id": 2, "complete": False},
                    {"id": 3, "complete": False}
                ]
            })

            leaderboard_entry = {
                "telegram_id": telegram_id,
                "username": username,
                "score": age,  # Initial score, you can modify this as per your requirements
                "position": 0  # This will be updated when fetching the leaderboard
            }
            leaderboard_collection.insert_one(leaderboard_entry)
            return JsonResponse({"status": "success", "message": "User and associated data created successfully"},
                                status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@csrf_exempt
def get_user(request, telegram_id):
    """Получение данных о пользователе"""
    if request.method == 'GET':
        try:
            # Получение пользователя
            user = users_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            return JsonResponse({"status": "success", "user": user}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@csrf_exempt
def update_balance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get("telegram_id")
            new_balance = data.get("balance")

            if new_balance is None:
                return JsonResponse({"status": "error", "message": "Balance is required"}, status=400)

            result = users_collection.find_one_and_update(
                {"telegram_id": telegram_id},
                {"$set": {"balance": new_balance}},
                return_document=ReturnDocument.AFTER
            )

            if not result:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            return JsonResponse({"status": "success", "message": "Balance updated successfully", "user": result}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
@csrf_exempt
def get_user_rewards(request, telegram_id):
    """Получение данных о наградах пользователя"""
    if request.method == 'GET':
        try:
            # Получение данных о наградах
            reward = rewards_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            if not reward:
                return JsonResponse({"status": "error", "message": "No rewards found"}, status=404)

            return JsonResponse({"status": "success", "reward": reward}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
@csrf_exempt
def get_user_frens(request, telegram_id):
    """Получение данных о друзьях пользователя"""
    if request.method == 'GET':
        try:
            # Получение данных о друзьях
            frens = frens_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            if not frens:
                return JsonResponse({"status": "error", "message": "No frens found"}, status=404)

            return JsonResponse({"status": "success", "frens": frens}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

@csrf_exempt
def get_user_tasks(request, telegram_id):
    """Получение данных о задачах пользователя"""
    if request.method == 'GET':
        try:
            # Получение данных о задачах
            tasks = tasks_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            if not tasks:
                return JsonResponse({"status": "error", "message": "No tasks found"}, status=404)

            return JsonResponse({"status": "success", "tasks": tasks}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import DESCENDING
import json

@csrf_exempt
def get_leaderboard(request):
    """
    Получение информации о доске лидеров и статистике пользователя.
    """
    try:
        # Получение всех записей из коллекции leaderboard и сортировка по убыванию score
        leaderboard_cursor = leaderboard_collection.find().sort("score", DESCENDING)

        # Преобразование записей в список с заменой ObjectId на строку
        leaderboard = [
            {
                "_id": str(entry["_id"]),
                "position": index + 1,
                "score": entry["score"],
                "telegram_id": entry["telegram_id"],
                "username": entry["username"]
            }
            for index, entry in enumerate(leaderboard_cursor)
        ]

        # Получение информации о текущем пользователе (замените 'your_telegram_id' на фактический идентификатор)
        user_telegram_id = request.GET.get("telegram_id")

        if user_telegram_id:
            try:
                user_telegram_id = str(user_telegram_id)
                print(user_telegram_id)
                user_entry = leaderboard_collection.find_one({"telegram_id": user_telegram_id})

                if user_entry:
                    user_stats = {
                        "position": next((i for i, entry in enumerate(leaderboard) if entry["telegram_id"] == user_telegram_id), None) + 1,
                        "score": user_entry["score"]
                    }
                else:
                    user_stats = {
                        "position": None,
                        "score": None
                    }
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid telegram_id format"}, status=400)
        else:
            user_stats = {
                "position": None,
                "score": None
            }

        return JsonResponse({
            "board": leaderboard,
            "count": len(leaderboard),
            "me": user_stats
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def insert_leaderboard_entry(entry):
    leaderboard_collection.insert_one(entry.to_dict())

from django.views.decorators.http import require_GET
@csrf_exempt
@require_GET
def get_user_stats(request, telegram_id):
    try:
        user_telegram_id = request.GET.get("user_id")
        if not user_telegram_id:
            return JsonResponse({"status": "error", "message": "user_id parameter is required"}, status=400)

        user_telegram_id = int(user_telegram_id)
        user = leaderboard_collection.find_one({"telegram_id": user_telegram_id})
        if not user:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)

        user_stats = {
            "position": user.get("position"),
            "score": user.get("score")
        }

        return JsonResponse(user_stats)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Function to update a user's score
def update_user_score(telegram_id, score):
    user = leaderboard_collection.find_one({'telegram_id': telegram_id})
    if user:
        leaderboard_collection.update_one({'telegram_id': telegram_id}, {'$set': {'score': score}})
    else:
        # Insert new entry if user does not exist
        new_entry = LeaderboardEntry(position=0, score=score, telegram_id=telegram_id, username='Unknown')
        insert_leaderboard_entry(new_entry)