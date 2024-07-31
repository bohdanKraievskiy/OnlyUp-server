from django.conf import settings

MONGO_DB = settings.MONGO_DB

class User:
    def __init__(self, username, age=0, avatar=None, balance=0.0, is_premium=False,
                 last_seen=None, reference=None, streak=None, telegram_id=None,
                 top_group=0, top_percent=0, wallet=None):
        self.username = username
        self.age = age
        self.avatar = avatar
        self.balance = balance
        self.is_premium = is_premium
        self.last_seen = last_seen
        self.reference = reference
        self.streak = streak
        self.telegram_id = telegram_id
        self.top_group = top_group
        self.top_percent = top_percent
        self.wallet = wallet

    def __str__(self):
        return self.username

class Reward:
    def __init__(self, telegram_id, age=0, boost=0, game=0.0, daily=0.0, frens=0.0,
                 premium=0, tasks=0, total=0.0):
        self.telegram_id = telegram_id
        self.age = age
        self.boost = boost
        self.game = game
        self.daily = daily
        self.frens = frens
        self.premium = premium
        self.tasks = tasks
        self.total = total


    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "age": self.age,
            "boost": self.boost,
            "game": self.game,
            "daily": self.daily,
            "frens": self.frens,
            "premium": self.premium,
            "tasks": self.tasks,
            "total": self.total,
        }

class Frens:
    def __init__(self, telegram_id, count=0, frens=None):
        if frens is None:
            frens = []
        self.telegram_id = telegram_id
        self.count = count
        self.frens = frens

    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "count": self.count,
            "frens": self.frens,
        }
class Task:
    def __init__(self, telegram_id, tasks=None):
        if tasks is None:
            tasks = []
        self.telegram_id = telegram_id
        self.tasks = tasks

    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "tasks": self.tasks,
        }

class LeaderboardEntry:
    def __init__(self, position, score, telegram_id, username):
        self.position = position
        self.score = score
        self.telegram_id = telegram_id
        self.username = username

    def to_dict(self):
        return {
            'position': self.position,
            'score': self.score,
            'telegram_id': self.telegram_id,
            'username': self.username
        }