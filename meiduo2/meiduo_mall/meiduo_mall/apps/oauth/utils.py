from urllib.request import urlopen

from django.conf import settings   # Django配置信息
import urllib.parse
import logging

from rest_framework.utils import json

from .exceptions import OAuthQQAPIError
from . import constants
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

logger = logging.getLogger("django")


class OAuthQQ(object):
    """
    QQ认证辅助工具
    """
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id or settings.QQ_CLIENT_ID
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE  # 用于保存成功后的跳转页面路径

        self.client_secret = client_secret if client_secret else settings.QQ_CLIENT_SECRET

    def get_login_url(self):
        """
        获取qq登录的网址
        :return: url网址
        """
        url = "https://graph.qq.com/oauth2.0/authorize?"
        params = {

            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": self.state
        }
        url += urllib.parse.urlencode(params)   # 把参数一查询字符串的格式传进去
        print(url)
        return url

    def get_access_token(self, code):
        """
        获取access_token
        :param code: qq提供的code
        :return: access_token
        """
        url = "https://graph.qq.com/oauth2.0/token?"

        params = {

            'grant_type': 'authorization_code',
            'client_id': self.client_id,        # 分配给网站的appid。
            'client_secret': self.client_secret,    # 分配给网站的appkey。
            'code': code,
            'redirect_uri': self.redirect_uri,
        }

        url += urllib.parse.urlencode(params)

        print(url)

        try:
            # 发送请求
            resp = urlopen(url)

            # 读取响应体数据
            resp_data = resp.read()   # bytes
            print(resp_data)
            resp_data = resp_data.decode()  # str
            print(resp_data)

   # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14

            # 解析 access_token
            resp_dict = urllib.parse.parse_qs(resp_data)
            print(resp_dict)
        except Exception as e:
            logger.error("获取access_token异常: %s" % e)
            raise OAuthQQAPIError

        else:
            access_token = resp_dict.get("access_token")
            print(access_token)
            return access_token[0]

    def get_openid(self, access_token):

        """
        获取用户的openid

        :param access_token: qq提供的access_token
        :return: open_id
        """

        url = "https://graph.qq.com/oauth2.0/me?access_token=" + access_token

        try:
            # 发送请求
            resp = urlopen(url)

            # 读取响应体数据
            resp_data = resp.read()  # bytes
            resp_data = resp_data.decode()  # str

            # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;

            # 解析
            resp_data = resp_data[10:-4]
            resp_dict = json.loads(resp_data)

        except Exception as e:
            logger.error("获取openid异常：%s"%e)
            raise OAuthQQAPIError
        else:
            openid = resp_dict.get("openid")
            print(openid)
            return openid


    def generate_bind_user_access_token(self, openid):

        """
         生成保存用户数据的token
        :param openid: 用户的openid
        :return: token
        """
        # serializer = Serializer(秘钥, 有效期秒)
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        print(serializer)

        # serializer.dump(数据) , 返回bytes类型
        token = serializer.dumps({'openid': openid})
        return token.decode()
    #
    # @staticmethod
    # def check_save_user_token(access_token):
    #     """
    #     检验保存用户数据的access_token
    #
    #     :return: openid or None
    #     """
    #     serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
    #     try:
    #         data = serializer.loads(access_token)
    #     except BadData:
    #         return None
    #
    #     else:
    #         return data.get("openid")
    #





    @staticmethod
    def check_bind_user_access_token(access_token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, constants.BIND_USER_ACCESS_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data['openid']






























