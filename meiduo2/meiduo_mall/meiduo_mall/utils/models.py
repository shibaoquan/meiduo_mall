


"""

1. 在user模型类里补充 两个字段create_time和update_time
2. 在oauth子应用中 创建一个新的用户QQ模型类表 并指定与user模型类的关系 定义QQ身份
3. 数据库迁移

"""

from django.db import models

class BaseModel(models.Model):

    """为模型类补充字段"""

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True  # 定义为抽象类, 用于继承使用，数据库迁移时不会创建BaseModel的表







