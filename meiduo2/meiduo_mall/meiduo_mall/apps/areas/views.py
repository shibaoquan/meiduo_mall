from rest_framework.viewsets import ReadOnlyModelViewSet
from areas.serializers import AreaSerializer, SubAreaSerializer
from .models import Area
from rest_framework_extensions.cache.mixins import CacheResponseMixin


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    # CacheResponseMixin 提供List和Retrieve两种缓存

    """
    行政区划信息
    """
    pagination_class = None  # 区划信息不分页

    def get_queryset(self):

        """
        提供数据
        """
        if self.action == "list":
            return Area.objects.filter(parent=None)  # 父类id为None的是省分
        else:
            return Area.objects.all()

    def get_serializer_class(self):

        """
        提供序列化器
        """
        if self.action == "list":
            return AreaSerializer

        else:
            return SubAreaSerializer


"""
    我们可以将省市区数据进行缓存处理，减少数据库的查询次数。

"""
