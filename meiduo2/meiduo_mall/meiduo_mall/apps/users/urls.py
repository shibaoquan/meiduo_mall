from django.conf.urls import url
from rest_framework import routers

from . import views
from rest_framework_jwt.views import obtain_jwt_token


# 创建路由
router = routers.DefaultRouter()
router.register(r"addresses", views.AddressViewSet, base_name="addresses")


urlpatterns = [

    url(r'^users/$', views.UserView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # url(r'^authorizations/$', obtain_jwt_token),  # 登录认证   签发JWT的视图 默认的返回值仅有token  还需在返回值中增加username和user_id。修改该视图的返回值
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),  # 登录认证, 补充了合并购物车功能

    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'^email/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),

    url(r'^users/(?P<pk>\d+)/password/$', views.ChangePassword.as_view()), # 修改密码

]

urlpatterns += router.urls

