# users/models.py
from pymongo import ReturnDocument
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
