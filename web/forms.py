from django import forms

from .models import KnowledgeNode, UserProfile


class ProfileForm(forms.ModelForm):
    """
    个人中心资料修改表单：
    - 昵称
    - 个性签名
    - 头像上传
    """

    class Meta:
        model = UserProfile
        fields = ["nickname", "bio", "avatar"]


class KnowledgeNodeForm(forms.ModelForm):
    """
    知识树节点创建表单：
    - 标题
    - 内容
    作者和父节点在视图中自动填充。
    """

    class Meta:
        model = KnowledgeNode
        fields = ["title", "content"]
