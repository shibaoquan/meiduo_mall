import base64
import pickle
from django.shortcuts import render

from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from carts.serializers import CartSerializer, CartSKUSerializer, CarDeleteSerializer, CartSelectSerializer
from goods import constants
from goods.models import SKU


class CartView(APIView):
    """
    购物车
    """

    def perform_authentication(self, request):
        """
        重写父类的验证方法, 不在进入视图前就检查JWT
        :param request:
        :return:
        """
        pass

    def post(self, request):
        """
        添加购物车

        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get("sku_id")
        count = serializer.validated_data.get("count")
        selected = serializer.validated_data.get("selected")

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录用redis保存
            redis_con = get_redis_connection("cart")
            pl = redis_con.pipeline()
            # 记录购物车商品数量
            pl.hincrby("cart_%s" % user.id, sku_id, count)  # hincrby根据HASH表的KEY，为KEY对应的VALUE自增参数VALUE。

            # 记录购物车的勾选项
            # 勾选
            if selected:
                pl.sadd("cart_selected_%s" % user.id, sku_id)

            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            # 用户未登录
            cart = request.COOKIES.get("cart")
            if cart is not None:
                # 使用pickle序列化购物车数据, pickle操作的是bytes类型的数据
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get('count'))

            cart[sku_id] = {
                "count": count,
                "selected": selected   #默认勾选
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 设置购物车的cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie("cart", cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
            return response


    def get(self, request):
        """
        查询购物车
        :return:
        """
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        # 如果登录 从redis中查询商品
        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            redis_cart = redis_conn.hgetall("cart_%s" % user.id)  # hgetall() 返回哈希表 key 中，所有的域和值。
            redis_cart_selected = redis_conn.smembers("cart_selected_%s" % user.id)  # 返回字典所有key

            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in redis_cart_selected
                }

        else:
            # 如果没有登录 从cookie查询商品
            cart = request.COOKIES.get("cart")
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

        # 遍历处理购物车数据
        skus = SKU.objects.filter(id__in=cart.keys())  # 得到大字典
        for sku in skus:
            sku.count = cart[sku.id]["count"]
            sku.selected = cart[sku.id]["selected"]

        serizlizer = CartSKUSerializer(skus, many=True)
        return Response(serizlizer.data)

    def put(self, request):
        """
        修改购物车
        :return:
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get("sku_id")
        count = serializer.validated_data.get("count")
        selected = serializer.validated_data.get("selected")

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录用redis保存
            redis_con = get_redis_connection("cart")
            pl = redis_con.pipeline()
            # 记录购物车商品数量
            pl.hset("cart_%s" % user.id, sku_id, count)

            # 勾选
            if selected:
                pl.sadd("cart_selected_%s" % user.id, sku_id)

            else:
                pl.srem("cart_selected_%s" % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)

        else:
            # 用户未登录
            cart = request.COOKIES.get("cart")
            if cart is not None:
                # 使用pickle序列化购物车数据, pickle操作的是bytes类型的数据
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get('count'))

            cart[sku_id] = {
                "count": count,
                "selected": selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 设置购物车的cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie("cart", cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
            return response

    def delete(self, request):
        """
        删除购物车数据
        :param request:
        :return:
        """

        serializer = CarDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data["sku_id"]

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录 在redis中保存
            redis_con = get_redis_connection("cart")
            pl = redis_con.pipeline()
            pl.hdel("cart_%s" % user.id, sku_id)  # 删除redis中的商品sku_id
            pl.srem("cart_selected_%s" % user.id, sku_id)  # 中选中字典中删除商品sku_id
            pl.execute()  # 执行管道
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:

            # 用户未登录, 在cookie中保存
            cookie_cart = request.COOKIES.get("cart")

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}
            response = Response(status=status.HTTP_204_NO_CONTENT)
            if sku_id in cart_dict:
                del cart_dict[sku_id]  # 删除
                cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置购物车的cookie长期有效
                response.set_cookie("cart", cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)

            return response

class CartSelectAllView(APIView):
    """
    购物车全选
    """
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法 不再进入视图前就检查JWT
        :return:
        """
        pass

    def put(self, request):
        serialzier = CartSelectSerializer(data=request.data)
        serialzier.is_valid(raise_exception=True)
        selected = serialzier.validated_data["selected"]

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录 在redis中保存
            redis_con = get_redis_connection("cart")
            cart = redis_con.hgetall("cart_%s"%user.id)
            sku_id_list = cart.keys()

            if selected:
                # 全选， 所有的sku_id都添加到redis set
                redis_con.sadd("cart_selected_%s"%user.id, *sku_id_list)
            else:
                # 取消全选, 清空redis中的set数据
                redis_con.srem("cart_selected_%s"%user.id, *sku_id_list)
            return Response({'message': 'OK'})

        else:
            # 用户未登录, 在cookie中保存
            cookie_cart = request.COOKIES.get("cart")
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))  # 解析

                # cart_dict = {
                #     sku_id_1: {
                #         'count': 10
                #         'selected': True
                #     },
                #     sku_id_2: {
                #         'count': 10
                #         'selected': False
                #     },
                # }

            else:
                cart_dict = {}

            response = Response({'message': 'OK'})
            if cart_dict:
                for count_selected_dict in cart_dict.values():
                    count_selected_dict["selected"] = selected
                cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)

            return response










