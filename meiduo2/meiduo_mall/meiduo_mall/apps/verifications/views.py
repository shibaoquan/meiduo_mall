import random

from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.utils.exceptions import logger
from meiduo_mall.utils.yuntongxun.sms import CCP
from verifications import constants
from . import constants, serializers

from celery_tasks.sms.tasks import send_sms_code   # 从celery包里把send_sms_code导出来


class ImageCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):
        """获取图片验证码"""

        # 生成图片验证码
        text, image = captcha.generate_captcha()
        # 连接redis
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)  # 参数: id 有效期 美容

        return HttpResponse(image, content_type="image/jpg")


class SMSCodeView(GenericAPIView):

    """短信验证码"""

    serializer_class = serializers.ImageCodeCheckSerializer  # 指定序列化器类

    def get(self, request, mobile):

        # 判断图片验证码是否在60s内
        serializer = self.get_serializer(data=request.query_params) # 反序列化 data=request.query_params是获取get请求中的参数, data作为反序化的数据
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = "%06d"% random.randint(0, 999999)
        print(sms_code)

        # 保存短信验证码 与 发送记录
        redis_conn = get_redis_connection("verify_codes")

        # redis管道
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()  # 让管道告诉redis执行命令


        # 发送短信验证码
        # try:
        #     expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)  #
        #     ccp = CCP()
        #     # result = ccp.send_template_sms(mobile, [sms_code, expires], SMS_CODE_TEMP_ID)
        #     result = ccp.send_template_sms(mobile, [sms_code, expires], 1)
        #
        # except Exception as e:
        #     logger.error("发送短信异常 [mobile: %s, message: %s]"% (mobile, e))
        #     return Response({"message": "falied"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #
        #
        # else:
        #     if result == 0:
        #         logger.info("发送短信正常[moblie:%s]"% mobile)
        #         return Response({"message": "OK"})
        #
        #     else:
        #         logger.error("发送短信异常 [mobile: %s]" % mobile)
        #         return Response({"message": "falied"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 使用celery发送短信
        expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        send_sms_code.delay(mobile, sms_code, expires, constants.SMS_CODE_TEMP_ID)

        return Response({"message": "OK"})


















































