from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("checkin/", views.daily_checkin, name="daily_checkin"),
    # 知识树
    path("world/", views.tree_index, name="tree_index"),
    path("node/<int:pk>/", views.node_detail, name="node_detail"),
    path("node/create/", views.create_node, name="create_node"),
    # 商店和背包
    path("shop/", views.shop_view, name="shop"),
    path("backpack/", views.inventory_view, name="inventory"),
    # 打赏功能
    path("transfer/", views.transfer_coins, name="transfer_coins"),
    # 房产系统
    path("buy-land/", views.buy_land, name="buy_land"),
    # AI助手
    path("ai-assistant/", views.ai_assistant, name="ai_assistant"),
    path("ai-chat/", views.ai_chat, name="ai_chat"),
]


