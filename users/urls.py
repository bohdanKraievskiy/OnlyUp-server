from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.create_user, name='create_user'),
    path('users/join/', views.get_user, name='get_user'),
    path('users/<str:telegram_id>/rewards/', views.get_user_rewards, name='get_user_rewards'),
    path('users/<str:telegram_id>/frens/', views.get_user_frens, name='get_user_frens'),
    path('users/<str:telegram_id>/tasks/', views.get_user_tasks, name='get_user_tasks'),
    path('users/update_balance/', views.update_balance, name='update_balance'),
    path('users/update_game_balance/', views.update_game_balance, name='update_game_balance'),
    path('users/update_attempts/', views.update_attempts, name='update_attempts'),
    path('leaderboard/', views.get_leaderboard, name='get_leaderboard'),
    path('account_date/insert/', views.insert_account_date, name='insert_account_date'),  # Updated path
    path('account_date/', views.get_account_date_by_telegram_id, name='get_account_date_by_telegram_id'),
    path('tasks/verify/', views.verify_task, name='verify_task'),  # New endpoint
    path('daily_reward/', views.daily_reward, name='daily_reward'),
    path('add_friend/', views.add_friend, name='add_friend')
]
