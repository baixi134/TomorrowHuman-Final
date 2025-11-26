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
]


