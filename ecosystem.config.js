module.exports = {
  apps: [
    {
      name: "django-app",
      script: "manage.py",
      args: "runserver 0.0.0.0:8000",
      interpreter: "python3",
      watch: true,
      env: {
        "DJANGO_SETTINGS_MODULE": "django_OnlyUp.settings",
        "PYTHONUNBUFFERED": "1"
      }
    }
  ]
}
