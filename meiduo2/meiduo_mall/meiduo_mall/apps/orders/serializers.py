from decimal import Decimal
# from time import timezone
from django.utils import timezone

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from goods.models import SKU
from meiduo_mall.utils.exceptions import logger
from orders.models import OrderInfo, OrderGoods
from django.db import transaction  # 导入事务模块


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label="数量")

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label="运费", max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    保存订单序列化器
    """

    class Meta:
        model = OrderInfo
        fields = ("order_id", "address", "pay_method")
        read_only_fields = ("order_id",)
        extra_kwargs = {
            "address": {
                "write_only": True,
                "required": True,
            },
            "pay_method": {
                "write_only": True,
                "required": True,
            }
        }

    def create(self, validated_data):
        """
        保存订单
        """
        # 获取当前用户
        user = self.context["request"].user

        # 生成订单编号
        # 组织订单编号 20170903153611+user.id
        # timezone.now()  -> datetime
        # time.strftime(format[,t]) 接收以时间元组，并返回以可读字符串表示的当地时间，格式由参数format决定
        # order_id = timezone.now().strftime("%Y%m%d%H%M%S") + ("%09d" % user.id)
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 保存订单基本信息数据OrderInfo
        address = validated_data["address"]
        pay_method = validated_data["pay_method"]

        # 生成订单
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()

            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(10),
                    freight=Decimal(10),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']

                )

                # 获取购物车信息
                redis_con = get_redis_connection("cart")
                redis_cart = redis_con.hgetall("cart_%s" % user.id)
                cart_selected = redis_con.smembers("cart_selected_%s" % user.id)

                # 将bytes类型转换成int类型
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                # 从redis中一次查出所有商品数据
                skus = SKU.objects.filter(id__in=cart_selected)

                # 遍历结算商品
                for sku in skus:
                    while True:
                        sku_count = cart[sku.id]  # 判断商品库存

                        origin_stock = sku.stock  # 原始库存
                        origin_sales = sku.sales  # 原始销量

                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)  # 回滚节点
                            raise serializers.ValidationError("商品库存不足")

                        # 演示并发下单
                        # import time
                        # time.sleep(5)

                        # 减少库存 增加销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 加入乐观锁, 根据原始库存条件更新, 返回更新的条目数
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock)

                        if ret == 0: # 说明没有更新,结束本次循环执行下一次
                            continue

                        # 累计商品的SPU 销量信息
                        sku.goods.sales += sku_count
                        sku.goods.save()

                        # 累计订单基本信息的数据
                        order.total_count += sku_count  # 累计总金额
                        order.total_amount += (sku.price * sku_count)  # 累计总额


                        # 保存订单商品数据
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        break # 更新成功


                    # 更新订单的金额数量信息
                    order.total_amount += order.freight
                    order.save()

            except serializers.ValidationError:
                raise
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)  # 回滚事务
                raise

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 删除redis中保存的购物车数据
            pl = redis_con.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem("cart_selected_%s" % user.id, *cart_selected)
            pl.execute()
            return order
