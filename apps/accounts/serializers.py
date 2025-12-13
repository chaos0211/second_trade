from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    注册序列化器：只要求 username + password
    其他字段可选，不做复杂校验
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "phone",
            "nickname",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
            "nickname": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    当前用户信息
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "email",
            "phone",
            "role",
            "credit_score",
            "balance",
            "trade_count",
            "good_rate",
            "is_email_verified",
            "is_phone_verified",
        ]


class AdminUserListSerializer(serializers.ModelSerializer):
    """平台管理员查看用户列表/详情使用"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "email",
            "phone",
            "role",
            "credit_score",
            "balance",
            "trade_count",
            "good_rate",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "updated_at",
        ]


class AdminUserWriteSerializer(serializers.ModelSerializer):
    """平台管理员创建 / 更新用户使用（不做复杂校验）"""

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "nickname",
            "email",
            "phone",
            "role",
            "credit_score",
            "balance",
            "trade_count",
            "good_rate",
            "is_active",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        user = User.objects.create_user(
            password=password or None,
            **validated_data,
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password is not None and password != "":
            instance.set_password(password)
        instance.save()
        return instance
