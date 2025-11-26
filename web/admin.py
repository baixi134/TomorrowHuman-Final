from django.contrib import admin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    以 Inline 方式在 User 后台中直接编辑游戏数据。
    """
    model = UserProfile
    can_delete = False
    fk_name = 'user'
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'coins', 'level', 'experience')
    search_fields = ('user__username', 'nickname')


class CustomUserAdmin(admin.ModelAdmin):
    """
    扩展原生 User 的后台展示，把 UserProfile 作为 Inline 挂上去。
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_staff', 'is_active')


# 重新注册 User，使其带有 Profile Inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
