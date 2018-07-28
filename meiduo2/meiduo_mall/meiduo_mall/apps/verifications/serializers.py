from django_redis import get_redis_connection
from rest_framework import serializers
from meiduo_mall.utils.exceptions import logger


# 定义序列化器类
class ImageCodeCheckSerializer(serializers.Serializer):
    """图片验证码校验序列化器类


    帮助视图完成 参数效验的工作, 简化视图
    """

    image_code_id = serializers.UUIDField()  # 添加不存在的字段, 用来校验
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):  # 对多个字段进行校验

        """校验"""

        image_code_id = attrs["image_code_id"]
        text = attrs["text"]

        # 查询真实图片验证码
        redis_conn = get_redis_connection('verify_codes')  # 连接到redis
        real_image_code_text = redis_conn.get('img_%s' % image_code_id) # 根据键名取出图片验证码

        if not real_image_code_text:
            raise serializers.ValidationError("图片验证失败")

        # 验证一次后就从redis删除图片验证码
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except Exception as e:
            logger.error(e)

        # 比较图片验证码
        real_image_code_text = real_image_code_text.decode()

        if real_image_code_text.lower() != text.lower():
            raise serializers.ValidationError("图片验证码错误")

        # 判断是否在60s以内
        # 知识点1: get_serializer()方法在创建序列化器对象的时候会补充 context属性
        #          context属性包含三个值: request formet view
        #  知识点2:
        # django 的类视图中, kwrags包含了路径提取出来的参数
        mobile = self.context["view"].kwargs["mobile"]   # 理解: 获取序列化器的视图对象中的mobile属性
        send_flag = redis_conn.get("send_flag_%s" % mobile)

        return attrs
