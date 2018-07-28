from django.conf.urls import url
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from goods import views

router = DefaultRouter()
router.register(r'skus/search', views.SKUSearchViewSet, base_name="skus_search")

urlpatterns =[
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),

]

router = DefaultRouter()
router.register(r'^skus/search/$', views.SKUSearchViewSet, base_name="skus_search")

urlpatterns += router.urls