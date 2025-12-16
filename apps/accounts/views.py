from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    AdminUserListSerializer,
    AdminUserWriteSerializer,
)

User = get_user_model()


class SimpleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    登录序列化器：
    在标准 JWT 的基础上，额外返回部分用户信息，方便前端使用。
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 在 token 里可以加入少量自定义字段（可选）
        token["username"] = user.username
        token["role"] = getattr(user, "role", "")
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 登录成功后额外返回一点用户信息
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "nickname": getattr(self.user, "nickname", ""),
            "email": self.user.email,
            "phone": getattr(self.user, "phone", None),
            "address": getattr(self.user, "address", None),
            "role": getattr(self.user, "role", ""),
        }
        return data


class SimpleTokenObtainPairView(TokenObtainPairView):
    """
    登录接口：POST username + password 获取 JWT
    """

    permission_classes = [AllowAny]
    serializer_class = SimpleTokenObtainPairSerializer


class RegisterAPIView(APIView):
    """
    注册接口：简单版本，不做复杂校验，只要用户名 + 密码必填。
    其他字段（邮箱、手机号、昵称等）可以按需传入。
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "注册成功",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "nickname": getattr(user, "nickname", ""),
                        "email": user.email,
                        "phone": getattr(user, "phone", None),
                        "address": getattr(user, "address", None),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    """
    获取当前登录用户信息
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


    def put(self, request):
        """更新当前登录用户信息（支持部分字段更新）。"""
        user = request.user
        data = request.data.copy()

        # 密码单独处理：避免明文落库
        raw_password = data.pop("password", None)

        serializer = UserProfileSerializer(user, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        if raw_password:
            user.set_password(raw_password)
            user.save(update_fields=["password"])

        # 重新序列化返回最新数据
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)




class IsPlatformAdmin(BasePermission):
    """仅允许 role=admin 的平台管理员访问"""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "admin")


class AdminUserViewSet(ModelViewSet):
    """平台管理员用户管理：增删改查（CRUD）"""

    queryset = User.objects.all().order_by("-id")
    permission_classes = [IsPlatformAdmin]

    def get_serializer_class(self):
        # 列表/详情使用只读序列化器；创建/更新使用写入序列化器
        if self.action in ("list", "retrieve"):
            return AdminUserListSerializer
        return AdminUserWriteSerializer

    def perform_destroy(self, instance):
        # 防止管理员误删自己（如需允许删除自己，可删除此判断）
        if instance.pk == self.request.user.pk:
            raise PermissionDenied("不能删除当前登录的管理员账号")
        super().perform_destroy(instance)


# 登出接口：通过拉黑 refresh token 实现登出。
# 前端需要在 body 中传 refresh token。
class LogoutAPIView(APIView):
    """
    登出接口：通过拉黑 refresh token 实现登出。
    前端需要在 body 中传 refresh token。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh)
            # 如果启用了 SimpleJWT blacklist，则会真正失效
            try:
                token.blacklist()
            except AttributeError:
                # 未启用 blacklist 时，忽略即可（由前端清理本地 token）
                pass
            return Response({"message": "ok"}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {"error": "invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
