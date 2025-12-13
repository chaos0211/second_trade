from django.db import models
from django.conf import settings


# 1. 设备基础库

class Category(models.Model):
    """
    设备分类，如 手机 / 平板 / 笔记本 / 配件 等
    """
    name = models.CharField(max_length=50, help_text="分类名称，如手机、平板")
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="分类编码，便于前端或运营配置（可选）",
    )
    description = models.TextField(
        blank=True,
        help_text="分类说明，例如主要面向的设备类型、典型品牌等",
    )
    icon = models.URLField(
        blank=True,
        null=True,
        help_text="分类图标 URL（可选）",
    )

    def __str__(self):
        return self.name


class Brand(models.Model):
    """
    品牌，如 Apple / Huawei / Xiaomi
    """
    name = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    logo = models.URLField(
        blank=True,
        null=True,
        help_text="品牌 Logo 地址（可选）",
    )
    description = models.TextField(
        blank=True,
        help_text="品牌介绍或备注说明",
    )

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class DeviceModel(models.Model):
    """
    具体设备型号，如 iPhone 13 / Mate 40 / iPad Pro 11
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="市场基准回收价（可根据官方或历史数据确定）",
    )
    release_date = models.DateField(
        null=True,
        blank=True,
        help_text="上市日期（用于估价时判断新旧程度）",
    )
    storage_spec = models.CharField(
        max_length=50,
        blank=True,
        help_text="存储规格，如 128GB / 256GB（可选）",
    )
    color = models.CharField(
        max_length=30,
        blank=True,
        help_text="官方主推颜色，如 星光色、远峰蓝（可选）",
    )
    is_discontinued = models.BooleanField(
        default=False,
        help_text="是否停产，用于估价与推荐策略",
    )
    official_url = models.URLField(
        blank=True,
        null=True,
        help_text="官方产品介绍链接（可选）",
    )

    def __str__(self):
        return f"{self.brand.name} {self.name}"


# 2. 估价规则体系

class ValuationOption(models.Model):
    """
    估价选项，如 屏幕状态 / 电池健康 / 是否维修
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # 例如 "屏幕状态"
    weight = models.FloatField(
        default=1.0,
        help_text="权重（用于估价算法加权）",
    )
    is_required = models.BooleanField(
        default=True,
        help_text="该估价选项是否为必选项",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="前端展示顺序，数值越小越靠前",
    )

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ValuationChoice(models.Model):
    """
    选项具体取值，如：
    屏幕状态：完美 / 细微划痕 / 明显划痕
    """
    option = models.ForeignKey(
        ValuationOption,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    content = models.CharField(max_length=100)
    depreciation_rate = models.FloatField(
        help_text="折旧率，例如 0.05 代表扣减 5%",
    )
    score = models.IntegerField(
        default=0,
        help_text="可选的评分值，用于统计或规则引擎（例如好=3，一般=1）",
    )

    def __str__(self):
        return f"{self.option.name} - {self.content}"


# 3. 商品与交易

class Product(models.Model):
    """
    二手商品信息：
    - 基本信息：标题、描述、所属型号
    - 价格信息：系统估价、卖家定价
    - 状态流转：草稿 / 上架 / 锁定 / 已售 / 已下架
    """

    STATUS_CHOICES = (
        ("draft", "草稿/估价中"),
        ("on_sale", "上架中"),
        ("locked", "交易中/已锁定"),
        ("sold", "已售出"),
        ("cancelled", "已下架"),
    )

    QUALITY_CHOICES = (
        ("A", "准新 / 轻微使用痕迹"),
        ("B", "正常使用痕迹"),
        ("C", "明显磨损但功能正常"),
        ("D", "功能/外观存在明显问题"),
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.PROTECT,
        help_text="关联的设备型号",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="系统估价（由估价引擎自动计算）",
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="卖家实际售价",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    quality_grade = models.CharField(
        max_length=1,
        choices=QUALITY_CHOICES,
        default="B",
        help_text="成色等级，便于前端筛选展示",
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="设备所在城市/地区，如 深圳市 南山区",
    )

    # 数据埋点 / 推荐用统计字段
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="浏览次数（可用于推荐与热度排序）",
    )
    favorite_count = models.PositiveIntegerField(
        default=0,
        help_text="被收藏次数",
    )
    is_recommended = models.BooleanField(
        default=False,
        help_text="是否为平台推荐商品",
    )

    # 存储估价问卷的选择，如 {"屏幕状态": "完美", "电池": "80%-90%"}
    condition_data = models.JSONField(
        default=dict,
        help_text="估价时用户选择的配置与成色快照（JSON）",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="商品创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="商品最近更新时间",
    )

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """
    商品图片表，一对多：
    - 支持多张图片
    - 标记主图
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField(
        help_text="图片 URL（前端或对象存储地址）",
    )
    is_main = models.BooleanField(
        default=False,
        help_text="是否为主图",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="图片排序，数值越小越靠前",
    )

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Image for {self.product_id}"


class Order(models.Model):
    """
    订单信息：
    - 订单状态流转
    - 买家 / 商品 / 金额
    - 收货与物流信息
    """

    STATUS_CHOICES = (
        ("pending_payment", "待支付"),
        ("paid", "已支付/待发货"),
        ("shipped", "已发货/待收货"),
        ("inspecting", "验机中"),
        ("completed", "已完成"),
        ("refunded", "已退款/取消"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("wechat", "微信支付"),
        ("alipay", "支付宝"),
        ("balance", "平台余额"),
    )

    order_no = models.CharField(
        max_length=32,
        unique=True,
        help_text="订单编号，可使用 UUID 等规则生成",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buy_orders",
    )
    product = models.OneToOneField(
        Product,
        on_delete=models.PROTECT,
        help_text="关联的商品，完成交易后商品即售出",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="订单金额（应付金额）",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending_payment",
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="balance",
        help_text="支付方式（可根据项目实际调整）",
    )
    shipping_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="物流单号（可选）",
    )
    logistics_company = models.CharField(
        max_length=50,
        blank=True,
        help_text="物流公司名称，如 顺丰 / 圆通",
    )

    # 收货信息（简化版）
    receiver_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="收货人姓名",
    )
    receiver_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="收货人手机号",
    )
    receiver_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="收货地址",
    )

    # 重要时间节点
    pay_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="支付时间",
    )
    ship_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="发货时间",
    )
    complete_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="订单完成时间",
    )
    cancel_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="订单取消/退款时间",
    )

    # 备注信息
    buyer_message = models.TextField(
        blank=True,
        help_text="买家留言",
    )
    seller_message = models.TextField(
        blank=True,
        help_text="卖家备注（仅后台可见）",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="订单创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="订单最近更新时间",
    )

    def __str__(self):
        return self.order_no