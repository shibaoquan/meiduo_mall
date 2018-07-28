
"""修改Django REST framework的默认异常处理方法，补充处理数据库异常和Redis异常。"""

from rest_framework.views import exception_handler as drf_exception_handler  # 导入框架原生的异常处理方法
import logging

from django.db import DatabaseError   # 导入数据库异常
from redis.exceptions import RedisError  # 导入redis异常
from rest_framework.response import Response
from rest_framework import status



# 获取在配置文件中定义的logger, 用来记录日志
logger = logging.getLogger('django')

def exception_handler(exc, context):
    """
    自定义异常处理
    :param exc: 异常
    :param context: 抛出异常的上下文
    :return: Response响应对象
    """

    # 调用drf框架原生的异常处理方法
    response = drf_exception_handler(exc, context)

    if response is None:
        view = context['view']  # 从异常上下文的字典中获取 异常的视图名字

        if isinstance(exc, DatabaseError)or isinstance(exc, RedisError):
            # 数据异常
            logger.error('[%s]%s'%(view, exc))
            response = Response({'message':'服务器内部错误'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

    return response


"""
drf_exception_handler:  是exception_handler改名字得来的, 他可以处理序列化器的异常信息返回响应对象response, 如果response为空表示,
捕获到的异常exception_handler处理不了, 此时需要我们重写exception_handler异常处理方法,添加数据库异常和redis异常的判断,并返回异常响应

"""


