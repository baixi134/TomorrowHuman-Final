import json
import os

import google.generativeai as genai
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

from .forms import KnowledgeNodeForm, ProfileForm
from .models import GameItem, KnowledgeNode, LandPlot, UserInventory, UserProfile

# 配置本地代理，解决国内无法访问 Google 的问题（必须在 genai.configure 之前）
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 加载环境变量并配置 Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def index(request):
    """
    赛博朋克虚拟广场首页：
    - 获取最近注册的20位用户
    - 展示在虚拟广场上
    - 获取所有地块信息
    """
    latest_users = User.objects.select_related('profile').order_by('-date_joined')[:20]
    # 确保所有用户都有profile（防止旧数据没有profile）
    for user in latest_users:
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
    
    # 获取所有地块，预加载 owner 和 owner.profile
    plots = LandPlot.objects.all().select_related('owner', 'owner__profile')
    
    # 确保所有地块的 owner 都有 profile（防止旧数据没有 profile）
    for plot in plots:
        if plot.owner and not hasattr(plot.owner, 'profile'):
            UserProfile.objects.create(user=plot.owner)
    
    # 获取当前用户ID（如果已登录）
    current_user_id = request.user.id if request.user.is_authenticated else None
    
    context = {
        "latest_users": latest_users,
        "plots": plots,
        "current_user_id": current_user_id,
    }
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
    # 使用 get_or_create 但不设置 defaults，避免重置已有数据
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

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
    # 获取或创建用户档案，避免重置已有数据
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

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
    知识宇宙可视化：构建完整的知识树数据，包含所有节点。
    创建一个虚拟的'超级根节点'，将所有真实根节点作为其子节点。
    """
    import json
    
    def build_node_tree(node):
        """递归构建节点树结构"""
        node_data = {
            'name': node.title,
            'value': node.pk,
            'author': node.author.username,
            'created_at': node.created_at.strftime('%Y-%m-%d %H:%M'),
            'content': node.content[:100] + '...' if len(node.content) > 100 else node.content,
        }
        
        # 递归获取所有子节点
        children = node.children.all().order_by('created_at')
        if children.exists():
            node_data['children'] = [build_node_tree(child) for child in children]
        
        return node_data
    
    # 获取所有根节点（parent=None）
    roots = KnowledgeNode.objects.filter(parent__isnull=True).select_related("author").order_by("-created_at")
    
    # 构建虚拟超级根节点
    if roots.exists():
        universe_data = {
            'name': '知识宇宙',
            'value': 0,
            'children': [build_node_tree(root) for root in roots]
        }
    else:
        # 如果没有节点，创建一个空的超级根节点
        universe_data = {
            'name': '知识宇宙',
            'value': 0,
            'children': []
        }
    
    # 直接传递字典对象，使用json_script过滤器在模板中处理
    context = {
        "universe_data": universe_data,
    }
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
            try:
                profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=request.user)
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


@login_required
def shop_view(request):
    """
    商店页面：
    - 展示所有 GameItem
    - 处理购买逻辑 (POST请求)
    - 支持分类筛选
    """
    # 获取分类筛选参数
    category = request.GET.get("category", "")
    
    # 获取所有商品
    items = GameItem.objects.all()
    
    # 如果指定了分类，进行筛选
    if category:
        items = items.filter(category=category)
    
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        if item_id:
            try:
                item = GameItem.objects.get(pk=item_id)
                # 获取或创建用户档案
                try:
                    profile = UserProfile.objects.get(user=request.user)
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=request.user)
                
                # 检查用户金币是否足够
                if profile.coins < item.price:
                    messages.error(request, "余额不足")
                else:
                    # 扣除金币
                    profile.coins -= item.price
                    profile.save()
                    
                    # 更新或创建背包记录
                    inventory, created = UserInventory.objects.get_or_create(
                        user=request.user,
                        item=item,
                        defaults={"quantity": 0}
                    )
                    inventory.quantity += 1
                    inventory.save()
                    
                    messages.success(request, f"购买成功！获得 {item.name}")
            except GameItem.DoesNotExist:
                messages.error(request, "道具不存在")
    
    # 获取分类选项
    categories = GameItem.CATEGORY_CHOICES
    
    context = {
        "items": items,
        "categories": categories,
        "current_category": category,
    }
    return render(request, "web/shop.html", context)


@login_required
def inventory_view(request):
    """
    背包页面：
    - 展示当前用户背包里 quantity > 0 的所有物品
    - 支持分类筛选
    """
    # 获取分类筛选参数
    category = request.GET.get("category", "")
    
    # 获取用户背包物品
    inventory_items = UserInventory.objects.filter(
        user=request.user,
        quantity__gt=0
    ).select_related("item")
    
    # 如果指定了分类，进行筛选
    if category:
        inventory_items = inventory_items.filter(item__category=category)
    
    # 获取分类选项
    categories = GameItem.CATEGORY_CHOICES
    
    context = {
        "inventory_items": inventory_items,
        "categories": categories,
        "current_category": category,
    }
    return render(request, "web/inventory.html", context)


@login_required
def transfer_coins(request):
    """
    打赏金币功能：
    - 接收 recipient_id (接收者ID) 和 amount (金额)
    - 检查当前用户余额是否充足
    - 如果充足则转账，否则提示余额不足
    """
    if request.method != "POST":
        return redirect("web:index")
    
    recipient_id = request.POST.get("recipient_id")
    amount = request.POST.get("amount")
    
    # 验证参数
    if not recipient_id or not amount:
        messages.error(request, "参数错误")
        return redirect("web:index")
    
    try:
        amount = int(amount)
        if amount <= 0:
            messages.error(request, "打赏金额必须大于0")
            return redirect("web:index")
    except (ValueError, TypeError):
        messages.error(request, "金额格式错误")
        return redirect("web:index")
    
    # 获取接收者
    try:
        recipient = User.objects.get(pk=recipient_id)
    except User.DoesNotExist:
        messages.error(request, "用户不存在")
        return redirect("web:index")
    
    # 检查是否是自己
    if recipient.id == request.user.id:
        messages.warning(request, "不能给自己转账")
        return redirect("web:index")
    
    # 获取或创建当前用户的档案
    try:
        sender_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        sender_profile = UserProfile.objects.create(user=request.user)
    
    # 检查余额是否充足
    if sender_profile.coins < amount:
        messages.error(request, "余额不足")
        return redirect("web:index")
    
    # 获取或创建接收者的档案
    try:
        recipient_profile = UserProfile.objects.get(user=recipient)
    except UserProfile.DoesNotExist:
        recipient_profile = UserProfile.objects.create(user=recipient)
    
    # 执行转账
    sender_profile.coins -= amount
    recipient_profile.coins += amount
    
    sender_profile.save()
    recipient_profile.save()
    
    messages.success(request, f"打赏成功！已向 {recipient_profile.nickname or recipient.username} 转账 {amount} 金币")
    
    return redirect("web:index")


@login_required
def buy_land(request):
    """
    购买地块功能：
    - 接收 plot_id (地块ID)
    - 检查地块是否有主（防止并发购买）
    - 检查用户金币是否足够
    - 交易执行：扣钱 -> 地块 owner 设为当前用户 -> 保存
    """
    if request.method != "POST":
        return redirect("web:index")
    
    plot_id = request.POST.get("plot_id")
    
    # 验证参数
    if not plot_id:
        messages.error(request, "参数错误")
        return redirect("web:index")
    
    try:
        plot = LandPlot.objects.get(pk=plot_id)
    except LandPlot.DoesNotExist:
        messages.error(request, "地块不存在")
        return redirect("web:index")
    
    # 检查地块是否有主
    if plot.owner is not None:
        messages.error(request, "该地块已被购买")
        return redirect("web:index")
    
    # 获取或创建当前用户的档案
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # 检查余额是否充足
    if profile.coins < plot.price:
        messages.error(request, f"余额不足！需要 {plot.price} 金币，您只有 {profile.coins} 金币")
        return redirect("web:index")
    
    # 执行购买（使用事务确保数据一致性）
    from django.db import transaction
    try:
        with transaction.atomic():
            # 再次检查地块是否有主（防止并发问题）
            plot.refresh_from_db()
            if plot.owner is not None:
                messages.error(request, "该地块已被其他玩家购买")
                return redirect("web:index")
            
            # 扣除金币
            profile.coins -= plot.price
            profile.save()
            
            # 设置地块拥有者
            plot.owner = request.user
            plot.save()
            
            messages.success(request, f"购买成功！您已获得地块：{plot.name}，花费 {plot.price} 金币")
    except Exception as e:
        messages.error(request, f"购买失败：{str(e)}")
    
    return redirect("web:index")


def ai_assistant(request):
    """
    AI助手页面（占位）
    """
    return render(request, "web/ai_assistant.html", {})


@login_required
@csrf_exempt
def ai_chat(request):
    """
    AI聊天接口：
    - 接收 POST 请求中的 message
    - 获取用户状态（金币、等级）
    - 调用 Gemini API 生成回复
    - 返回 JSON 响应
    """
    if request.method != "POST":
        return JsonResponse({"error": "只支持 POST 请求"}, status=405)
    
    try:
        # 解析请求数据
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        
        if not message:
            return JsonResponse({"error": "消息不能为空"}, status=400)
        
        # 获取用户状态
        try:
            profile = UserProfile.objects.get(user=request.user)
            coins = profile.coins
            level = profile.level
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
            coins = profile.coins
            level = profile.level
        
        # 构建提示词
        prompt = f"""你是一个赛博朋克虚拟世界的 AI 助手，名字叫 CyberBot。你的说话风格要酷一点、简短一点，带一点未来感。当前对话的用户拥有 {coins} 金币，等级是 Lv.{level}。如果用户问怎么赚钱，就推荐他去签到或买地皮。用户的输入是：{message}"""
        
        try:
            print("--- 正在尝试连接 Gemini... ---")  # 打印调试信息
            model = genai.GenerativeModel('models/gemini-2.0-flash')
            response = model.generate_content(prompt)
            ai_reply = response.text
            print(f"--- Gemini 回复成功: {ai_reply[:20]}... ---")  # 打印成功信息
            return JsonResponse({'response': ai_reply})
        
        except Exception as e:
            # 【重点】把错误原因打印在终端里！
            print(f"!!! 严重错误: {type(e).__name__} !!!")
            print(f"错误详情: {e}")
            return JsonResponse({'response': f'系统连接中断: {str(e)}'})
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "请求数据格式错误"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"服务器错误：{str(e)}"}, status=500)
