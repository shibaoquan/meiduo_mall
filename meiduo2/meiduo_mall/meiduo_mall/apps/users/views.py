from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from carts.utils import merge_cart_cookie_to_redis
from .models import User
from django.shortcuts import render
from rest_framework import status, mixins
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users import constants, serializers
from rest_framework_jwt.views import ObtainJSONWebToken



class UsernameCountView(APIView):

    """用户名数量"""

    def get(self, request, username):

        """获取指定用户名数量"""

        count = User.objects.get(username=username).count()

        data = {
            "username": username,
            "count": count
        }
        return Response(data)



class MobileCountView(APIView):

    """用户手机号数量"""


    def get(self, request, mobile):

        """获取指定手机号数量"""

        count = User.objects.get(mobile=mobile).count()

        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data)


class UserView(CreateAPIView):

    """
    用户注册

    传入参数:
        username, password, password2, sms_code, moblie, allow
    """

    serializer_class = serializers.CreateUserSerializer


class UserDetailView(RetrieveAPIView):

    """
    用户详情
    """

    serializer_class = serializers.UserDetailSerializer
    permission_classes = [IsAuthenticated]  # 验证过的


    def get_object(self):

        # 返回当前请求的用户
        # 在类视图中 可以通过类视图对象的属性获取request
        # 在django的请求request对象中, user属性表明当前请求的用户
        return self.request.user


class EmailView(UpdateAPIView):

    """
    保存用户的邮箱信息
    """

    permission_classes = [IsAuthenticated] # 验证通过的
    serializer_class = serializers.EmailSerializer

    def get_object(self, *args, **kwargs):

        return self.request.user


# url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
class VerifyEmailView(APIView):

    """
    邮箱验证
    """

    def get(self, request):

        # 获取token
        token = request.query_params.get("token")
        if not token:
            return Response({"message": "缺少token"})

        user = User.check_verify_email_token(token)
        if user is None:

            return Response({"message": "链接无效"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            user.email_active = True
            user.save()
            return Response({"message": "OK"})


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)  ### 为什么是addresses ???

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializers = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            "user_id": user.id,
            "default_address_id": user.default_address_id,
            "limit": constants.USER_ADDRESS_COUNTS_LIMIT,
            "addresses": serializers.data,
        })

    @action(methods=["put"], detail=True)
    def status(self, request, *args, **kwargs):

        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({"message": "保存用户数据已达到上限"}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """
    def post(self, request, *args, **kwargs):
        # 调用父类的方法, 获取drf jwt扩展默认的认证用户处理结果
        response = super().post(request, *args, **kwargs)

        # 仿照drf jwt扩展对于用户登录的认证方式，判断用户是否认证登录成功
        # 如果用户登录认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get("user")

            response = merge_cart_cookie_to_redis(request, user, response)

        return response


class ChangePassword(mixins.UpdateModelMixin, GenericAPIView):
    """
    修改密码
    """
    serializer_class = serializers.ChangePasswordSerializer
    queryset = User.objects.all()

    def post(self, request, pk):
        return self.update(request, pk)










































