from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        # 导入信号处理函数，确保 User 创建时自动创建 UserProfile
        from . import signals  # noqa: F401
