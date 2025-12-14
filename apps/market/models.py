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
    """商品图片表（本地上传到 media/products/）。

    约定：
    - 数据库存储图片文件名（image_name），不是完整路径/URL
    - 文件名为随机/加密命名后的 .jpg，例如："8f3c...a9.jpg"
    - 完整访问地址在 API 里通过 settings.MEDIA_URL + "products/" + image_name 拼接
    """

    # 支持“渐进式上架”：先上传图片，不强制绑定商品
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
        help_text="可先上传图片不绑定商品，后续再关联到草稿商品",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_product_images",
        help_text="上传者",
    )
    # 草稿键：用于一次“上架流程”的临时会话/草稿（前端生成 uuid 传入）
    # 规则：同一 draft_key 下最多 4 张图；主图建议用 is_main=True 或 sort_order=0
    draft_key = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        default="",
        help_text="上架草稿键（uuid），用于在未创建商品前暂存图片",
    )

    # 只存文件名（不含目录、不含 URL）
    image_name = models.CharField(
        max_length=255,
        help_text="加密/随机命名后的 jpg 文件名，如 3b2f...e9.jpg",
    )

    # 可选元信息
    original_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="原始文件名（可选）",
    )
    size_bytes = models.PositiveIntegerField(
        default=0,
        help_text="文件大小（字节，可选）",
    )

    is_main = models.BooleanField(
        default=False,
        help_text="是否为主图",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="图片排序，数值越小越靠前",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="上传时间",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["uploaded_by", "draft_key"]),
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self):
        return self.image_name


# --- 识别/估价/比价相关模型 ---

class RecognitionResult(models.Model):
    """图像识别结果快照（只识别主图/第一张图）。

    说明：
    - 不强行做“成色判断”，成色由估价问卷（ValuationOption/Choice）负责
    - 识别结果主要用于：判断大类/品牌/型号（可为空，支持用户手动选择）
    - detections 用于前端展示识别可视化结果（bbox/label/confidence）
    """

    image = models.OneToOneField(
        ProductImage,
        on_delete=models.CASCADE,
        related_name="recognition",
    )

    ok = models.BooleanField(default=False, help_text="是否识别成功")

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="识别出的分类（可空）",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="识别出的品牌（可空）",
    )
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="识别出的型号（可空）",
    )

    confidence = models.FloatField(default=0.0, help_text="识别置信度 0~1")
    detections = models.JSONField(
        default=list,
        help_text="检测框列表（label/confidence/bbox 等），用于前端展示",
    )
    message = models.CharField(max_length=200, blank=True, help_text="识别说明/失败原因")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RecognitionResult(image_id={self.image_id}, ok={self.ok})"


class ValuationSnapshot(models.Model):
    """估价快照（建议售价/区间/比价都从这里或 MarketPriceStat 推导）。

    典型流程：
    - 前端提交：device_model + choice_ids
    - 后端计算：estimated_price + breakdown
    - 再结合 MarketPriceStat 算：market_diff_pct / value_score 等
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="valuation_snapshots",
        help_text="发起估价的用户",
    )

    # 允许先估价不创建商品；确认上架时再绑定到 Product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="valuation_snapshots",
        help_text="关联商品（可空）",
    )

    device_model = models.ForeignKey(DeviceModel, on_delete=models.PROTECT)
    choice_ids = models.JSONField(default=list, help_text="用户选择的 ValuationChoice id 列表")

    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="系统估价金额",
    )

    # 估价明细：每个选项/choice/折旧率/权重等
    breakdown = models.JSONField(default=list, help_text="估价明细（JSON）")

    # 用于前端展示：建议售价区间（可选）
    suggested_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    suggested_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 用于“高于/低于市场价”的展示（可选缓存字段）
    market_median = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    market_diff_pct = models.FloatField(default=0.0, help_text="(selling - median)/median")
    value_score = models.FloatField(default=0.0, help_text="(median - selling)/median，越大越划算")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ValuationSnapshot(id={self.id}, price={self.estimated_price})"


class MarketPriceStat(models.Model):
    """市场价格统计（用于比价与性价比排序）。

    简化方案：
    - p10/p50/p90 表示低价/中位/高价
    - 初期可用“平台成交价”聚合统计生成；后期可接入爬虫/第三方价格源
    """

    device_model = models.OneToOneField(
        DeviceModel,
        on_delete=models.CASCADE,
        related_name="market_price",
    )

    p10_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    p50_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    p90_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    sample_size = models.PositiveIntegerField(default=0, help_text="统计样本量")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MarketPriceStat({self.device_model_id})"


# --- 瑕疵项 / 成色（新三步上架方案） ---

class DefectItem(models.Model):
    """类别维度的“检查项”（至少 3 项/类目），用于：

    - 前端步骤2：展示系统识别的检查项（屏幕/机身/镜头/接口/按键等）
    - 识别只输出：每个检查项的损耗程度（0/1/2/3）与可视化框

    注意：这里不做型号识别；检查项仅与 Category 绑定。
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="defect_items",
        help_text="所属设备类别",
    )

    code = models.CharField(
        max_length=32,
        help_text="检查项编码（建议英文小写/下划线），如 screen / body / lens / port / joystick",
    )
    name = models.CharField(
        max_length=50,
        help_text="检查项名称，如 屏幕 / 机身 / 镜头 / 接口 / 摇杆",
    )

    # 识别/质检提示
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="检查项说明（给前端提示用，可选）",
    )

    # 是否必检、排序
    is_required = models.BooleanField(default=True, help_text="是否为必检项")
    sort_order = models.PositiveIntegerField(default=0, help_text="前端展示顺序")

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["category", "code"], name="uniq_defectitem_category_code"),
        ]

    def __str__(self):
        return f"{self.category.name}-{self.name}"


class DefectSeverity(models.Model):
    """某个检查项的“损耗程度”（用于步骤2 输出与步骤3 估价扣减）。

    level 约定：
    - 0: 无问题（通常不入库，前端可直接显示 0）
    - 1: 轻微
    - 2: 明显
    - 3: 严重

    penalty_weight：用于估价扣减（0~1），例如屏幕严重碎裂可到 0.25~0.35。
    """

    defect_item = models.ForeignKey(
        DefectItem,
        on_delete=models.CASCADE,
        related_name="severities",
    )

    level = models.PositiveSmallIntegerField(help_text="损耗等级：1/2/3")
    label = models.CharField(max_length=30, help_text="等级名称，如 轻微/明显/严重")

    penalty_weight = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        help_text="扣减权重（0~1），用于估价算法",
    )

    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="对该等级的解释说明（可选）",
    )

    class Meta:
        ordering = ["defect_item", "level", "id"]
        constraints = [
            models.UniqueConstraint(fields=["defect_item", "level"], name="uniq_defectseverity_item_level"),
        ]

    def __str__(self):
        return f"{self.defect_item.name}-{self.label}"


class ConditionGrade(models.Model):
    """“几成新/新旧程度”选项（每个类目一套）。

    用于：步骤2 最后一行展示“几成新”，步骤3 根据 grade_factor 参与估价。
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="condition_grades",
    )

    # 例如：99新/95新/9成新/8成新...
    label = models.CharField(max_length=20, help_text="显示文本，如 9成新")

    # 例如：0.83
    factor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="成色系数（0~1），用于估价算法",
    )

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["category", "label"], name="uniq_conditiongrade_category_label"),
        ]

    def __str__(self):
        return f"{self.category.name}-{self.label}"


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