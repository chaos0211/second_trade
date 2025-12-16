from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    自定义用户模型：
    - 继承 AbstractUser，保留用户名、密码、邮箱、权限等鉴权字段
    - 追加交易平台相关的业务字段
    """

    # 角色类型：可以根据论文需要描述为买家/卖家/双重角色
    ROLE_CHOICES = (
        ("user", "普通用户"),
        ("admin", "管理员"),
    )

    # 基础扩展信息
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="手机号（可选）",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="默认收货/发货地址",
    )
    nickname = models.CharField(
        max_length=30,
        blank=True,
        help_text="用户昵称，用于前端展示",
    )
    avatar = models.URLField(
        blank=True,
        null=True,
        help_text="头像图片地址（URL）",
    )

    # 角色与状态
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="user",
        help_text="用户在平台中的角色类型",
    )

    # 交易与信用体系
    credit_score = models.IntegerField(
        default=100,
        help_text="平台内部信用积分，初始值可设为 100",
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10000.00,
        help_text="平台账户余额，用于收款 / 退款等",
    )
    trade_count = models.PositiveIntegerField(
        default=0,
        help_text="累计成功交易订单数",
    )
    good_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="好评率，例如 98.50 表示 98.50%",
    )

    # 简单的实名/安全扩展（可选，用于论文描述“安全性设计”）
    is_email_verified = models.BooleanField(
        default=True,
        help_text="邮箱是否已通过验证",
    )
    is_phone_verified = models.BooleanField(
        default=True,
        help_text="手机号是否已通过验证",
    )

    # 更新时间戳：便于审计与运营分析
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="用户信息最近更新时间",
    )

    def update_credit(self, points: int):
        """
        更新用户信用积分（可正可负）。
        可在交易完成、投诉、违约等场景中调用。
        """
        self.credit_score += points
        self.save(update_fields=["credit_score"])

    def increase_trade_count(self):
        """
        成交订单数 +1，可在订单完成时调用。
        """
        self.trade_count += 1
        self.save(update_fields=["trade_count"])

    def __str__(self):
        # 优先展示昵称/用户名，便于后台查看
        return self.nickname or self.username or f"User<{self.pk}>"
