from decimal import Decimal

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders import serializers
from orders.serializers import OrderSettlementSerializer


class OrderSettlementView(APIView):
    """
    订单结算
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        """
        获取
        """
        user = request.user

        # 从购物车中获取用户勾选要结算的商品
        redis_con = get_redis_connection("cart")
        redis_cart = redis_con.hgetall("cart_%s" % user.id)
        redis_selectetd = redis_con.smembers("cart_selected_%s" % user.id)

        cart = {}

        # 遍历勾选列表 被勾选的商品加入到cart里
        for sku_id in redis_selectetd:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询数据库商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal("10.00")

        seriliazer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(seriliazer.data)


class SaveOrderView(CreateAPIView):
    """
    保存订单
    """
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.SaveOrderSerializer
