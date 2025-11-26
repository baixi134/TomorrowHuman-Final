from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import KnowledgeNodeForm, ProfileForm
from .models import KnowledgeNode, UserProfile


def index(request):
    """
    简单首页：
    - 已登录：显示“你好，[用户名]”
    - 未登录：显示“请登录”
    """
    context = {}
    if request.user.is_authenticated:
        context["message"] = f"你好，{request.user.username}"
    else:
        context["message"] = "请登录"
    return render(request, "web/index.html", context)


def register_view(request):
    """
    使用 Django 自带的 UserCreationForm 处理注册。
    注册成功后跳转到登录页。
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("web:login")
    else:
        form = UserCreationForm()

    return render(request, "web/register.html", {"form": form})


def login_view(request):
    """
    使用 Django 自带的 AuthenticationForm 处理登录。
    登录成功后跳转到首页。
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("web:index")
    else:
        form = AuthenticationForm(request)

    return render(request, "web/login.html", {"form": form})


def logout_view(request):
    """
    处理登出并跳转到登录页。
    """
    logout(request)
    return redirect("web:login")


@login_required
def profile_view(request):
    """
    个人中心：
    - 展示头像、等级、金币、经验条
    - 允许修改昵称、签名和头像
    """
    # 理论上通过 signals 已自动创建 UserProfile，这里再保险一次
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
    else:
        form = ProfileForm(instance=profile)

    # 一个简单的经验条计算示例：假设每级 100 经验
    exp_for_next_level = 100
    exp_in_current_level = profile.experience % exp_for_next_level
    exp_percent = max(
        0,
        min(100, int(exp_in_current_level / exp_for_next_level * 100)),
    )

    context = {
        "profile": profile,
        "form": form,
        "exp_percent": exp_percent,
    }
    return render(request, "web/profile.html", context)


@login_required
def daily_checkin(request):
    """
    每日签到功能：
    - 检查用户今天是否已经签到
    - 如果未签到，增加金币和经验值
    """
    # 获取或创建用户档案
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # 获取今天的日期
    today = timezone.now().date()

    # 检查今天是否已经签到
    if profile.last_checkin == today:
        messages.warning(request, "今天已经签到过了，明天再来吧！")
    else:
        # 签到成功，增加奖励
        profile.coins += 10
        profile.experience += 5
        profile.last_checkin = today
        profile.save()
        messages.success(request, "签到成功！金币+10，经验+5")

    # 重定向回之前的页面，如果没有则返回首页
    return redirect(request.META.get("HTTP_REFERER", "/"))


def tree_index(request):
    """
    知识树首页：展示所有根节点（parent=None），按时间倒序。
    """
    roots = (
        KnowledgeNode.objects.filter(parent__isnull=True)
        .select_related("author")
        .order_by("-created_at")
    )
    context = {"nodes": roots}
    return render(request, "web/tree_index.html", context)


def node_detail(request, pk: int):
    """
    节点详情页：展示当前节点及其直接子节点。
    """
    node = get_object_or_404(
        KnowledgeNode.objects.select_related("author"), pk=pk
    )
    children = node.children.select_related("author").order_by("created_at")
    context = {
        "node": node,
        "children": children,
    }
    return render(request, "web/node_detail.html", context)


@login_required
def create_node(request):
    """
    创建知识树节点：
    - 如果 URL/querystring 中带有 parent 或 parent_id，则视为回复指定父节点
    - 成功发布后给予用户 5 个金币作为贡献奖励
    """
    # 支持 query 参数 ?parent=ID 或 ?parent_id=ID
    parent_id = (
        request.GET.get("parent_id")
        or request.GET.get("parent")
    )
    parent_node = None
    if parent_id:
        parent_node = get_object_or_404(KnowledgeNode, pk=parent_id)

    if request.method == "POST":
        form = KnowledgeNodeForm(request.POST)
        if form.is_valid():
            node = form.save(commit=False)
            node.author = request.user

            # POST 时，也允许通过隐藏字段 parent_id 传参作为兜底
            post_parent_id = request.POST.get("parent_id")
            if post_parent_id:
                parent_node = get_object_or_404(KnowledgeNode, pk=post_parent_id)

            if parent_node:
                node.parent = parent_node

            node.save()

            # 贡献知识奖励：金币 +5
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.coins += 5
            profile.save()
            messages.success(request, "发布成功！贡献知识奖励：金币 +5")

            return redirect("web:node_detail", pk=node.pk)
    else:
        form = KnowledgeNodeForm()

    context = {
        "form": form,
        "parent": parent_node,
    }
    return render(request, "web/create_node.html", context)
