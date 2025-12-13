from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterAPIView, SimpleTokenObtainPairView, ProfileAPIView

urlpatterns = [
    # 注册
    path("register", RegisterAPIView.as_view(), name="register"),
    # 登录（获取 access / refresh）
    path("login", SimpleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # 刷新 access token
    path("refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # 当前用户信息
    path("me", ProfileAPIView.as_view(), name="profile"),
]