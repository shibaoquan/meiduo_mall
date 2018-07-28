import re

from rest_framework_jwt.settings import api_settings

from .models import User, Address  # 导入用户类
from django_redis import get_redis_connection
from rest_framework import serializers
from .models import User
from celery_tasks.email.tasks import send_verify_email



class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""

    # 添加User模型类没有的字段
    password2 = serializers.CharField(label="确认密码", write_only=True)
    sms_code = serializers.CharField(label="短信验证码", write_only=True)
    allow = serializers.CharField(label="是否同意用户协议", write_only=True)

    # 签发jwt token
    token = serializers.CharField(label="jwt token", read_only=True)

    class Meta:

        model = User
        fields = ("id", "username", "password", "password2", "sms_code", "mobile", "allow", "token")

        # 使用extra_kwargs参数为ModelSerializer添加或修改原有的选项参数
        extra_kwargs = {

            "username": {
                "min_length": 5,
                "max_length": 20,
                "error_messages": {
                    "min_length": "仅允许5-20个字符的用户名",
                    "max_length": "仅允许5-20个字符的用户名",
                }
            },

            "password": {
                "write_only": True,
                "min_length": 8,
                "max_length": 20,
                "error_messages": {
                    "max_length": "仅允许8-20个字符的密码",
                    "min_length": "仅允许8-20个字符的密码"
                }
            }

        }

    # 知识点: validate_ 验证单个字段
    def validate_mobile(self, value):

        """验证手机号码"""

        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("手机号格式错误")

        return value

    def valitae_allow(self, value):

        """检验用户是否同意协议"""

        if value != "true":
            raise serializers.ValidationError("请同意用户协议")
        return value

    # 知识点: validate() 验证多个字段
    def validate(self, data):

        """判断两次密码"""

        if data['password'] != data['password2']:
            raise serializers.ValidationError("两次密码不一致")

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get("sms_%s" % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError("无效的短信验证码")

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError("短信验证码错误")

        return data

    def create(self, validated_data):

        """创建用户"""

        # 移除数据库模型中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data["allow"]

        user = super().create(validated_data)

        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 签发jwt token  # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)


        # 在返回的user对象添加 jwt token属性
        user.token = token


        return user







class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):

    """
    邮箱序列化器类
    """

    class Meta:
        model = User
        fields = ("id", "email")

        extea_kwargs = { # 修改原有的选项参数
            "email": {
                "required": True
            }
        }

    def update(self, instance, validated_data):
        """instance为要更新的对象实例"""

        email = validated_data["email"]
        instance.email = email
        instance.save()

        # 生成验证链接
        verify_url = instance.generate_verify_email_url()
        # 发送验证邮件
        send_verify_email.delay(email, verify_url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):

    """
    用户地址序列化器
    """

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label="省ID", required=True)
    city_id = serializers.IntegerField(label="市ID", required=True)
    district_id = serializers.IntegerField(label="区ID", required=True)

    class Meta:
        model = Address

        exclude = ("user", "is_deleted", "create_time", "update_time")

    def validate_mobile(self, value):

        """
        验证手机号
        """

        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("手机号格式错误")

        return value

    def create(self, validated_data):

        """
        保存
        """

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):

    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ("title",)




class ChangePasswordSerializer(serializers.ModelSerializer):
    """
    修改密码序列化器
    """
    password1 = serializers.IntegerField(label="新密码", write_only=True)
    password2 = serializers.IntegerField(label="确认密码", write_only=True)


    class Meta:
        model = User
        fields = ("password", "password1", "password2")

        extra_kwargs = {
            "password1": {
                "min_length": 8,
                "max_length": 20,
                "error_messages": {
                    "max_length": "仅允许8-20个字符的密码",
                    "min_length": "仅允许8-20个字符的密码"
                }
            }
        }

    # 验证
    def validate(self, attrs):

        password = attrs["password"]
        password1 = attrs["password2"]
        password2 = attrs["password2"]

        # 原始密码从数据库查user
        # user = User.objects.get(password=password)
        # print(user)

        user = True

        # 判断原始密码是否正确
        if user is not None:

            if password1 != password2:
                raise serializers.ValidationError("两次输入的密码不一致")

        else:
            # 密码错误
            raise serializers.ValidationError("密码错误")

        return attrs



    def update(self, instance, validated_data):
        """
        更新密码
        """
        # 调用django 用户模型类的设置密码方法
        instance.set_password(validated_data['password'])
        instance.save()
        return instance














































































