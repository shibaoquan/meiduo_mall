import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并请求用户的购物车数据, 将未登录的cookie中的数据保存到redis里
    :param request:用户的请求对象
    :param user:当前登录的用户
    :param resopnse:响应对象，用于清除购物车cookie
    :return:

    合并前
    redis_cart = {
        '1': '20',
        '2': '2',
        '3': '5'
    }
    redis_cart_selected = set(1, 3)

    cookie_cart = {
        1: {
            'count': 10,
            'selected': False
        },
        4: {
            'count': 6,
            'selected': True
        }
    }
    合并后
    redis_cart = {
        '1': '10',
        '2': '2',
        '3': '5',
        '4': '6',
    }
    redis_cart_selected = set(3, 4)
    """


    cookie_cart = request.COOKIES.get("cart")
    if cookie_cart is not None:

        cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

        #  获取redis中的购物车商品数量数据, hash
        redis_con = get_redis_connection("cart")
        redis_cart = redis_con.hgetall("cart_%s"%user.id)

        # 用来存储redis最终保存的商品数量信息的hash数据
        cart = {}
        for sku_id, count in redis_cart.items():
            cart[int(sku_id)] = int(count)
        # 用来记录redis最终操作时，哪些sku_id是需要勾选新增的
        redis_cart_selected_add = []

        # 用来记录redis最终操作时，哪些sku_id是需要取消勾选删除的
        redis_cart_selected_remove = []

        # 遍历cookie中的购物车
        # cookie_cart_dict = {
        #     sku_id_1: {
        #         'count': 10
        #         'selected': True
        #     },
        #     sku_id_2: {
        #         'count': 10
        #         'selected': False
        #     },
        # }

        for sku_id, count_selected_dict in cookie_cart_dict.items():
            #  处理商品的数量，维护在redis中购物车数据数量的最终字典
            cart[sku_id] = count_selected_dict["count"]

            # 处理商品的勾选状态
            if count_selected_dict["selected"]:
                # 如果cookie指明，勾选
                redis_cart_selected_add.append(sku_id)

            else:
                # 如果cookie指明，不勾选
                redis_cart_selected_remove.append(sku_id)

        if cart:
            pl = redis_con.pipeline()
            pl.hmset("cart_%s"%user.id, cart)

            if redis_cart_selected_remove:
                pl.srem('cart_selected_%s' % user.id, *redis_cart_selected_remove)
            if redis_cart_selected_add:
                pl.sadd('cart_selected_%s' % user.id, *redis_cart_selected_add)

            pl.execute()

        # 删除cookie
        response.delete_cookie("cart")
    return response
































