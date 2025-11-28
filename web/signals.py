from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    每当创建新的 User 时，自动创建对应的 UserProfile。
    """
    if created:
        UserProfile.objects.create(user=instance)


# 移除此信号处理器，避免每次 User 保存时都保存 profile
# 这可能导致数据被意外重置
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """
#     当 User 保存时，确保其 Profile 也能被正确保存（如果已存在）。
#     """
#     # 如果首次创建时已经在上面的 signal 里创建，这里只负责保证后续修改时 profile 会跟着保存
#     if hasattr(instance, 'profile'):
#         instance.profile.save()


