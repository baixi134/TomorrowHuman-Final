from django.contrib import admin
from django.contrib.auth.models import User

from .models import GameItem, LandPlot, UserInventory, UserProfile


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


@admin.register(GameItem)
class GameItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'effect_value')
    search_fields = ('name', 'description')
    list_filter = ('category', 'price',)


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'quantity')
    search_fields = ('user__username', 'item__name')
    list_filter = ('item',)


@admin.register(LandPlot)
class LandPlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'x_pos', 'y_pos', 'owner', 'building_type', 'price', 'is_for_sale', 'resale_price')
    search_fields = ('name', 'owner__username')
    list_filter = ('building_type', 'is_for_sale', 'owner')
    list_editable = ('is_for_sale',)


class CustomUserAdmin(admin.ModelAdmin):
    """
    扩展原生 User 的后台展示，把 UserProfile 作为 Inline 挂上去。
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_staff', 'is_active')


# 重新注册 User，使其带有 Profile Inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
