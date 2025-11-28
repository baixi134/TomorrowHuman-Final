from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    扩展 Django 原生 User 的虚拟世界属性。
    """
    # 关联到原生 User，用户删除时级联删除 Profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # 基础信息
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="头像")
    nickname = models.CharField(max_length=50, blank=True, verbose_name="昵称")

    # 游戏属性
    coins = models.IntegerField(default=100, verbose_name="游戏币")
    level = models.IntegerField(default=1, verbose_name="等级")
    experience = models.IntegerField(default=0, verbose_name="经验值")
    last_checkin = models.DateField(null=True, blank=True, verbose_name="上次签到日期")

    # 描述
    bio = models.TextField(blank=True, verbose_name="个性签名")

    def __str__(self):
        return self.nickname or self.user.get_username()

    class Meta:
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"


class KnowledgeNode(models.Model):
    """
    知识树节点：
    - author: 发表该观点的用户
    - title: 标题
    - content: 详细观点内容
    - parent: 父节点，空表示根话题
    - created_at: 创建时间
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="knowledge_nodes",
        verbose_name="作者",
    )
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="父节点",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "知识节点"
        verbose_name_plural = "知识节点"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.title} (子节点)"
        return self.title


class GameItem(models.Model):
    """
    游戏道具：
    - name: 道具名称
    - description: 描述
    - price: 价格
    - image: 道具图片
    - effect_value: 效果数值（预留字段）
    - category: 分类
    """
    CATEGORY_CHOICES = [
        ("equipment", "装备"),
        ("armor", "防具"),
        ("food", "食物"),
        ("item", "道具"),
        ("medicine", "药品"),
    ]
    
    name = models.CharField(max_length=100, verbose_name="道具名称")
    description = models.TextField(verbose_name="描述")
    price = models.IntegerField(verbose_name="价格")
    image = models.ImageField(upload_to="items/", blank=True, null=True, verbose_name="道具图片")
    effect_value = models.IntegerField(default=0, verbose_name="效果数值")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="item",
        verbose_name="分类"
    )

    class Meta:
        verbose_name = "游戏道具"
        verbose_name_plural = "游戏道具"
        ordering = ["category", "price"]

    def __str__(self):
        return self.name


class UserInventory(models.Model):
    """
    用户背包：
    - user: 关联 User
    - item: 关联 GameItem
    - quantity: 数量
    - 约束: 确保同一个用户同一个道具只有一条记录
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        verbose_name="用户"
    )
    item = models.ForeignKey(
        GameItem,
        on_delete=models.CASCADE,
        related_name="inventory_records",
        verbose_name="道具"
    )
    quantity = models.IntegerField(default=0, verbose_name="数量")

    class Meta:
        verbose_name = "用户背包"
        verbose_name_plural = "用户背包"
        unique_together = [["user", "item"]]
        ordering = ["-quantity", "item__name"]

    def __str__(self):
        return f"{self.user.username} - {self.item.name} x{self.quantity}"


class LandPlot(models.Model):
    """
    地块模型：
    - name: 地块名称
    - x_pos: 横坐标 (0-100)
    - y_pos: 纵坐标 (0-100)
    - owner: 拥有者（可为空，表示无主之地）
    - price: 系统初始售价
    - building_type: 建筑类型
    - is_for_sale: 是否正在转售
    - resale_price: 玩家转手挂单的价格
    """
    BUILDING_TYPE_CHOICES = [
        ('NONE', '空地'),
        ('APARTMENT', '胶囊公寓'),
        ('VILLA', '霓虹别墅'),
        ('TOWER', '摩天大楼'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="地块名称")
    x_pos = models.IntegerField(verbose_name="横坐标", help_text="0-100之间的整数")
    y_pos = models.IntegerField(verbose_name="纵坐标", help_text="0-100之间的整数")
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="land_plots",
        verbose_name="拥有者"
    )
    price = models.IntegerField(verbose_name="系统初始售价")
    building_type = models.CharField(
        max_length=20,
        choices=BUILDING_TYPE_CHOICES,
        default='NONE',
        verbose_name="建筑类型"
    )
    is_for_sale = models.BooleanField(default=False, verbose_name="是否正在转售")
    resale_price = models.IntegerField(null=True, blank=True, verbose_name="转售价格")

    class Meta:
        verbose_name = "地块"
        verbose_name_plural = "地块"
        ordering = ["name"]

    def __str__(self):
        return self.name
