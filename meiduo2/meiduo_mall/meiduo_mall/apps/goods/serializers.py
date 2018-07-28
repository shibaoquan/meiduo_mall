from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from goods.models import SKU
from goods.search_indexes import SKUIndex


class SKUSerializer(serializers.ModelSerializer):
    """
    SKU序列化器
    """

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """

    class Meta:
        index_classes = [SKUIndex]  # 指定索引类
        fields = ('text', 'id', 'name', 'price', 'default_image_url', 'comments')
        # fields属性的字段名与SKUIndex类的字段对应。


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    保存用户浏览历史记录序列化器
    """
    pass