from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from datetime import datetime
from .models import LeaderboardEntry,DateOfCreation
from pymongo import ReturnDocument
from pymongo import DESCENDING
from bson import ObjectId
# Получение коллекции пользователей
users_collection = settings.MONGO_DB['users']
rewards_collection = settings.MONGO_DB['rewards']
frens_collection = settings.MONGO_DB['frens']
tasks_collection = settings.MONGO_DB['tasks']
leaderboard_collection = settings.MONGO_DB['leaderboard']
accounts_dates_collection = settings.MONGO_DB["accountsDates"]
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
            top_group = data.get("top_group", 0)
            top_percent = data.get("top_percent", 0)
            is_premium = data.get("is_premium", False)
            # Проверка на существование пользователя
            existing_user = users_collection.find_one({"telegram_id": telegram_id})
            if existing_user:
                return JsonResponse({"status": "error", "message": "User already exists"}, status=400)
            balance = age

            # Проверка на премиум и добавление бонусов
            premium_bonus = 1000 if is_premium else 0
            balance += premium_bonus
            # Создание объекта User
            new_user = {
                "username": username,
                "telegram_id": telegram_id,
                "age": age,
                "avatar": None,
                "balance": balance,
                "is_premium": data.get("is_premium", False),
                "last_seen": datetime.now(),
                "last_reward_date" : datetime.now(),
                "reference": data.get("reference", None),
                "streak": 0,
                "top_group": top_group,
                "top_percent": top_percent,
                "wallet": None,
                "attempts_left": 20
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
                "premium": premium_bonus,
                "tasks": 0,
                "total": age + premium_bonus
            })
            frens_collection.insert_one({"telegram_id": telegram_id, "count": 0, "frens": []})

            tasks_collection.insert_one({
                "telegram_id": telegram_id,
                    "tasks" : [
                        {"title": "Follow OnlyUP on X", "url": "https://twitter.com/OnlyUP1B", "reward": "+1000",
                         "completed": False},
                        {"title": "Join our telegram chat", "url": "https://t.me/OnlyUP_Official_chat",
                         "reward": "+1000", "completed": False},
                        {"title": "OnlyUp Community", "url": "https://t.me/OnlyUP_Announcements", "reward": "+1000",
                         "completed": False}
                ]
            })

            leaderboard_entry = {
                "telegram_id": telegram_id,
                "username": username,
                "score": balance,  # Initial score, you can modify this as per your requirements
                "position": 0  # This will be updated when fetching the leaderboard
            }
            leaderboard_collection.insert_one(leaderboard_entry)
            return JsonResponse({"status": "success", "message": "User and associated data created successfully"},
                                status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@csrf_exempt
def get_user(request):
    """Получение данных о пользователе"""
    if request.method == 'POST':
        try:
            # Parse the JSON body
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            # Extract telegram_id from the JSON data
            telegram_id = body_data.get('user_id')
            if not telegram_id:
                return JsonResponse({"status": "error", "message": "user_id is required"}, status=400)

            # Find the user by telegram_id
            user = users_collection.find_one({"telegram_id": telegram_id})
            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

                # Check if the user is now premium and update balance if they were not premium before
                if user.get('is_premium', False):
                    rewards = rewards_collection.find_one({"telegram_id": telegram_id})
                    if rewards:
                        # If the user was not premium before, apply the premium bonuses
                        if not rewards.get('premium_bonus_applied', False):
                            users_collection.update_one(
                                {"telegram_id": telegram_id},
                                {"$inc": {"balance": +1000}}
                            )

                            rewards_collection.update_one(
                                {"telegram_id": telegram_id},
                                {"$inc": {"premium": 1000}, "$set": {"premium_bonus_applied": True}}
                            )

            now = datetime.utcnow()
            users_collection.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"last_seen": now}}
            )
            user = users_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            return JsonResponse({"status": "success", "user": user}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)
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
            update_user_score(telegram_id,new_balance)
            if telegram_id is None or new_balance is None:
                return JsonResponse({"status": "error", "message": "Telegram ID and balance are required"}, status=400)

            # Update the user's balance
            result = users_collection.find_one_and_update(
                {"telegram_id": int(telegram_id)},
                {"$set": {"balance": new_balance}},
                return_document=ReturnDocument.AFTER
            )

            if not result:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            # Convert ObjectId to string for JSON serialization
            result['_id'] = str(result['_id'])

            return JsonResponse({"status": "success", "message": "Balance updated successfully", "user": result}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
@csrf_exempt
def update_game_balance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get("telegram_id")
            new_balance = data.get("balance")
            scoreRef=data.get("scoreRef")
            update_user_score(telegram_id,new_balance)
            if telegram_id is None or new_balance is None:
                return JsonResponse({"status": "error", "message": "Telegram ID and balance are required"}, status=400)

            # Update the user's balance
            result = users_collection.find_one_and_update(
                {"telegram_id": int(telegram_id)},
                {"$set": {"balance": new_balance}},
                return_document=ReturnDocument.AFTER
            )

            if not result:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            # Convert ObjectId to string for JSON serialization
            result['_id'] = str(result['_id'])
            rewards_data = rewards_collection.find_one({"telegram_id": int(telegram_id)})
            if not rewards_data:
                # If no reward document exists, create one
                rewards_collection.insert_one({
                    "telegram_id": telegram_id,
                    "age": 0,
                    "boost": 0,
                    "game": +scoreRef,
                    "daily": 0.0,
                    "frens": 0.0,
                    "premium": 0,
                    "tasks": 0,
                    "total": +scoreRef
                })
            else:
                # Update existing rewards
                rewards_collection.update_one(
                    {"telegram_id": telegram_id},
                    {"$inc": {
                        "game": +scoreRef,
                        "total": +scoreRef
                    }}
                )
            return JsonResponse({"status": "success", "message": "Balance updated successfully", "user": result}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
@csrf_exempt
def update_rewards(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get("telegram_id")
            task_title = data.get("task_title")
            reward_value = data.get("reward_value")

            if telegram_id is None or task_title is None or reward_value is None:
                return JsonResponse({"status": "error", "message": "Telegram ID, task title, and reward value are required"}, status=400)

            # Find the user's rewards
            user_rewards = rewards_collection.find_one({"telegram_id": telegram_id})

            if not user_rewards:
                # If no rewards document exists, create one
                user_rewards = {
                    "telegram_id": telegram_id,
                    "tasks": {task_title: reward_value},
                    "total": reward_value
                }
                rewards_collection.insert_one(user_rewards)
            else:
                # Update the rewards document
                tasks_rewards = user_rewards.get("tasks", {})
                tasks_rewards[task_title] = tasks_rewards.get(task_title, 0) + reward_value
                total_rewards = sum(tasks_rewards.values())

                rewards_collection.find_one_and_update(
                    {"telegram_id": telegram_id},
                    {"$set": {"tasks": tasks_rewards, "total": total_rewards}},
                    return_document=ReturnDocument.AFTER
                )

            return JsonResponse({"status": "success", "message": "Rewards updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

@csrf_exempt
def get_user_rewards(request, telegram_id):
    """Получение данных о наградах пользователя"""
    if request.method == 'GET':
        try:
            # Получение данных о наградах
            reward = rewards_collection.find_one({"telegram_id": int(telegram_id)}, {"_id": 0})
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
            frens = frens_collection.find_one({"telegram_id": int(telegram_id)}, {"_id": 0})
            if not frens:
                return JsonResponse({"status": "error", "message": "No frens found"}, status=404)

            frens = frens_collection.find_one({"frens": int(telegram_id)}, {"_id": 0})
            if not frens:
                return JsonResponse({"status": "error", "message": "No frens found in frens collections"}, status=404)

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
            tasks_data = tasks_collection.find_one({"telegram_id": int(telegram_id)}, {"_id": 0})
            if not tasks_data or not tasks_data.get("tasks"):
                return JsonResponse({"status": "error", "message": "No tasks found"}, status=404)

            # Extract tasks and transform them to include title, URL, and completion status
            tasks = [
                {
                    "title": task.get("title", "Unknown Task"),
                    "url": task.get("url", "#"),
                    "reward": task.get("reward", "+0"),
                    "completed": task.get("completed", False)
                }
                for task in tasks_data["tasks"]
            ]

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
                user_telegram_id = int(user_telegram_id)
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
    user = leaderboard_collection.find_one({'telegram_id': int(telegram_id)})
    if user:
        leaderboard_collection.update_one({'telegram_id': int(telegram_id)}, {'$set': {'score': score}})
    else:
        # Insert new entry if user does not exist
        new_entry = LeaderboardEntry(position=0, score=score, telegram_id=telegram_id, username='Unknown')
        insert_leaderboard_entry(new_entry)


@csrf_exempt
def insert_account_date(request):
    """Insert account creation date into accountsDates collection."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get("telegram_id")
            date_str = data.get("date")
            if not telegram_id or not date_str:
                return JsonResponse({"status": "error", "message": "Missing telegram_id or date"}, status=400)

            existing_record = accounts_dates_collection.find_one({"telegram_id": telegram_id})
            if existing_record:
                return JsonResponse({"status": "error", "message": "Record with this telegram_id already exists"},
                                    status=400)

            # Convert date string to datetime object
            date = datetime.strptime(date_str, "%Y-%m-%d")

            account_date = DateOfCreation(telegram_id, date)
            accounts_dates_collection.insert_one(account_date.to_dict())

            return JsonResponse({"status": "success", "message": "Account date inserted successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@csrf_exempt
def get_account_date_by_telegram_id(request):
    """Retrieve account creation date by telegram_id."""
    if request.method == 'GET':
        try:
            telegram_id = request.GET.get("telegram_id")
            if telegram_id is None:
                return JsonResponse({"status": "error", "message": "telegram_id parameter is required"}, status=400)

            # Validate and convert telegram_id to integer
            try:
                telegram_id = int(telegram_id)
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid telegram_id format"}, status=400)
            account_date = accounts_dates_collection.find_one({"telegram_id": int(telegram_id)}, {"_id": 0})

            if not account_date:
                return JsonResponse({"status": "error", "message": "Account date not found"}, status=404)

            return JsonResponse({"status": "success", "account_date": account_date}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def verify_task(request):
    """Verify and update the completion status of a task for a user."""
    if request.method == 'POST':
        try:
            # Retrieve the telegram_id and task_title from the request body
            data = json.loads(request.body)
            telegram_id = data.get("telegram_id")
            task_title = data.get("task")
            reward_value = data.get("reward")
            if not telegram_id or not task_title:
                return JsonResponse({"status": "error", "message": "Missing telegram_id or task"}, status=400)

            # Find the user's tasks in the database
            tasks_data = tasks_collection.find_one({"telegram_id": telegram_id}, {"_id": 0})
            if not tasks_data or not tasks_data.get("tasks"):
                return JsonResponse({"status": "error", "message": "No tasks found for this user"}, status=404)

            # Update the task completion status
            task_updated = False
            for task in tasks_data["tasks"]:
                if task.get("title") == task_title:
                    task["completed"] = True
                    task_updated = True
                    break

            if not task_updated:
                return JsonResponse({"status": "error", "message": "Task not found"}, status=404)

            # Save the updated tasks back to the database
            tasks_collection.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"tasks": tasks_data["tasks"]}}
            )
            rewards_data = rewards_collection.find_one({"telegram_id": telegram_id})
            if not rewards_data:
                # If no reward document exists, create one
                rewards_collection.insert_one({
                    "telegram_id": telegram_id,
                    "age": 0,
                    "boost": 0,
                    "game": 0.0,
                    "daily": 0.0,
                    "frens": 0.0,
                    "premium": 0,
                    "tasks": +reward_value,
                    "total": +reward_value
                })
            else:
                # Update existing rewards
                rewards_collection.update_one(
                    {"telegram_id": telegram_id},
                    {"$inc": {
                        "tasks": +reward_value,
                        "total": +reward_value
                    }}
                )
            return JsonResponse({"status": "success", "tasks": tasks_data["tasks"]}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
from datetime import datetime, timedelta


@csrf_exempt
def daily_reward(request):
    """Endpoint to handle daily reward claim"""
    if request.method == 'POST':
        try:
            # Parse the JSON body
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)

            # Extract telegram_id from the JSON data
            telegram_id = body_data.get('telegram_id')
            if not telegram_id:
                return JsonResponse({"status": "error", "message": "Telegram ID is required"}, status=400)

            # Find the user by telegram_id
            user = users_collection.find_one({"telegram_id": telegram_id})
            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            # Check last reward date
            last_reward_date = user.get('last_reward_date')
            current_date = datetime.now().date()  # Use date() to get a datetime.date object

            if last_reward_date:
                last_reward_date = last_reward_date.date()

            # Calculate streak and reward
            if last_reward_date is None or current_date > last_reward_date:
                streak = user.get('streak', 0)

                if last_reward_date == current_date - timedelta(days=1):
                    # Increment streak if the last reward date was yesterday
                    streak += 1
                else:
                    # Reset streak if it's a new day and no streak
                    streak = 1

                # Update the user's streak, balance, and last_reward_date
                reward = calculate_reward(streak)
                new_balance = user.get('balance', 0) + reward

                # Update the database with new streak and balance
                result = users_collection.find_one_and_update(
                    {"telegram_id": telegram_id},
                    {"$set": {
                        "streak": streak,
                        "balance": new_balance,
                        "last_reward_date": datetime.now(),
                        "attempts_left": 20
                    }},
                    return_document=ReturnDocument.AFTER
                )

                rewards_data = rewards_collection.find_one({"telegram_id": telegram_id})
                if not rewards_data:
                    # If no reward document exists, create one
                    rewards_collection.insert_one({
                        "telegram_id": telegram_id,
                        "age": 0,
                        "boost": 0,
                        "game": 0.0,
                        "daily": +reward,
                        "frens": 0.0,
                        "premium": 0,
                        "tasks": 0,
                        "total": +reward
                    })
                else:
                    # Update existing rewards
                    rewards_collection.update_one(
                        {"telegram_id": telegram_id},
                        {"$inc": {
                            "daily": +reward,
                            "total": +reward
                        }}
                    )
                # Serialize updated user for JSON response
                result = serialize_user(result)

                return JsonResponse({
                    "status": "success",
                    "message": "Daily reward claimed successfully",
                    "streak": streak,
                    "reward": reward,
                    "user": result
                }, status=200)

            else:
                # If the user has already claimed today's reward
                return JsonResponse({
                    "status": "error",
                    "message": "Reward already claimed today",
                    "last_reward_date": last_reward_date.strftime('%Y-%m-%d')  # Ensure date is serialized
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

def calculate_reward(streak):
    """Calculate reward based on streak"""
    # Example reward calculation
    base_reward = 100
    return base_reward * streak

# Helper function to serialize dates
def serialize_user(user):
    """Convert datetime.date fields to strings for JSON serialization."""
    if 'last_reward_date' in user and isinstance(user['last_reward_date'], datetime):
        user['last_reward_date'] = user['last_reward_date'].strftime('%Y-%m-%d')

    if 'last_seen' in user and isinstance(user['last_seen'], datetime):
        user['last_seen'] = user['last_seen'].strftime('%Y-%m-%d')

    user['_id'] = str(user['_id'])  # Convert ObjectId to string
    return user
def reset_attempts_if_needed(self):
        current_time = datetime.now()
        if self.last_seen.date() < current_time.date():
            self.attempts_left = 20
            self.last_seen = current_time
            self.save()

def use_attempt(self):
    self.reset_attempts_if_needed()
    if self.attempts_left > 0:
        self.attempts_left -= 1
        self.save()
        return True
    return False


@csrf_exempt
def update_attempts(request):
    """Update user attempts based on their actions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            telegram_id = data.get('telegram_id')
            action = data.get('action')  # 'use' or 'reset'

            if not telegram_id or action not in ['use', 'reset']:
                return JsonResponse({"status": "error", "message": "Invalid input"}, status=400)

            # Find the user by telegram_id
            user = users_collection.find_one({"telegram_id": telegram_id})
            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            current_time = datetime.now()
            last_seen = user.get('last_seen', None)

            if isinstance(last_seen, str):
                last_seen_date = datetime.strptime(last_seen, '%Y-%m-%d').date()
            elif isinstance(last_seen, datetime):
                last_seen_date = last_seen.date()
            else:
                last_seen_date = current_time.date() - timedelta(days=1)  # Default to one day ago if last_seen is missing or in an unexpected format

            # Check if attempts need to be reset
            if last_seen_date < current_time.date():
                # Reset attempts
                users_collection.update_one(
                    {"telegram_id": telegram_id},
                    {"$set": {
                        "attempts_left": 20,
                        "last_seen": current_time.strftime('%Y-%m-%d')
                    }}
                )
                last_seen_date = current_time.date()  # Update the last_seen_date after resetting

            # Perform action
            if action == 'use':
                if user.get('attempts_left', 0) > 0:
                    users_collection.update_one(
                        {"telegram_id": telegram_id},
                        {"$inc": {"attempts_left": -1}}
                    )
                    # Fetch the updated user data
                    user = users_collection.find_one({"telegram_id": telegram_id})
                    return JsonResponse({"status": "success", "attempts_left": user.get('attempts_left')}, status=200)
                else:
                    return JsonResponse({"status": "error", "message": "No attempts left"}, status=400)

            elif action == 'reset':
                users_collection.update_one(
                    {"telegram_id": telegram_id},
                    {"$set": {"attempts_left": 20}}
                )
                # Fetch the updated user data
                user = users_collection.find_one({"telegram_id": telegram_id})
                return JsonResponse({"status": "success", "attempts_left": user.get('attempts_left')}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)
