from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import SKUSerializer, SKUIndexSerializer, AddUserBrowsingHistorySerializer
from drf_haystack.viewsets import HaystackViewSet
from .models import SKU


class SKUListView(ListAPIView):
    """
     商品列表视图
    """

    serializer_class = SKUSerializer
    filter_backends = (OrderingFilter,)  # 排序的支持
    ordering_fields = ("create_time", "price", "sales") # 指明了可以进行排序的字段

    def get_queryset(self):
        category_id = self.kwargs["category_id"]
        return SKU.objects.filter(category_id=category_id, is_launched=True)



class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer



class UserBrowsingHistoryView(CreateAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        """
        保存
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.create(request)
















