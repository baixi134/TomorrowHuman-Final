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
