from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.create_user, name='create_user'),
    path('users/<str:telegram_id>/', views.get_user, name='get_user'),
    path('users/<str:telegram_id>/rewards/', views.get_user_rewards, name='get_user_rewards'),
    path('users/<str:telegram_id>/frens/', views.get_user_frens, name='get_user_frens'),
    path('users/<str:telegram_id>/tasks/', views.get_user_tasks, name='get_user_tasks'),
    path('users/update_balance/', views.update_balance, name='update_balance'),
    path('leaderboard/', views.get_leaderboard, name='get_leaderboard'),
]
