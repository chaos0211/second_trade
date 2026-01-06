from rest_framework import serializers
from decimal import Decimal

from django.utils import timezone
from zoneinfo import ZoneInfo
from apps.market.models import Brand

from .models import (
    Category,
    DeviceModel,
    Product,
    ProductImage,
    ConditionGrade,
    Order,
    ValuationOption,
    ValuationChoice,
)

# --- market 下拉选项序列化器（给前端 Step1 使用） ---

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "code"]


class DeviceModelSerializer(serializers.ModelSerializer):
    # 前端用 brand_id 对接 category_id
    brand_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceModel
        fields = ["id", "name", "brand_id"]

# --- 兼容旧版 market/views.py 的序列化器（保留，避免后端起不来） ---

class ValuationRequestSerializer(serializers.Serializer):
    """旧版 ValuationAPI 入参：设备型号 + 估价选项选择"""

    device_model_id = serializers.IntegerField()
    choice_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class ProductCreateSerializer(serializers.ModelSerializer):
    """旧版 ProductViewSet 创建商品用（DRF ModelViewSet）"""

    class Meta:
        model = Product
        fields = [
            "device_model",
            "title",
            "description",
            "selling_price",
            "condition_data",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """旧版 OrderViewSet 用"""

    class Meta:
        model = Order
        fields = "__all__"

class OrderDetailSerializer(serializers.ModelSerializer):
    # Embed key product fields for frontend order/payment pages
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_main_image = serializers.SerializerMethodField()
    product_selling_price = serializers.DecimalField(source="product.selling_price", max_digits=10, decimal_places=2, read_only=True)
    seller_id = serializers.IntegerField(source="product.seller_id", read_only=True)
    seller_name = serializers.SerializerMethodField()
    buyer_address = serializers.CharField(source="buyer.address", read_only=True)
    seller_address = serializers.CharField(source="product.seller.address", read_only=True)

    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "status",
            "buyer_id",
            "buyer_address",
            "seller_id",
            "seller_name",
            "seller_address",
            "product_id",
            "product_title",
            "product_main_image",
            "product_selling_price",
            "created_at",
        ]

    def get_product_main_image(self, obj):
        try:
            img = obj.product.images.order_by("sort_order", "id").first()
            if not img:
                return None
            return f"/media/products/{img.image_name}"
        except Exception:
            return None

    def get_seller_name(self, obj):
        try:
            seller = obj.product.seller
            # Prefer nickname (nick_name), then username
            nick = getattr(seller, "nickname", None)
            if nick:
                return nick
            return getattr(seller, "username", None)
        except Exception:
            return None

    def get_created_at(self, obj):
        dt = getattr(obj, "created_at", None)
        if not dt:
            return None
        try:
            bj = ZoneInfo("Asia/Shanghai")
        except Exception:
            bj = None
        try:
            dt_local = timezone.localtime(dt, bj) if bj else timezone.localtime(dt)
        except Exception:
            dt_local = dt
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")

class DraftInitSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    device_model_id = serializers.IntegerField(required=False, allow_null=True)
    years_used = serializers.FloatField(min_value=0, max_value=20)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class UploadImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

class AnalyzeResultSerializer(serializers.Serializer):
    grade_label = serializers.CharField()
    grade_score = serializers.IntegerField()
    defects = serializers.ListField(child=serializers.CharField())

class EstimateSerializer(serializers.Serializer):
    # 可允许前端传 grade_label（用 AI 输出的）或 grade_id（从表选）
    grade_label = serializers.CharField(required=False, allow_blank=True)
    grade_id = serializers.IntegerField(required=False, allow_null=True)

class PublishSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    seller_id = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    seller_address = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    device_model_id = serializers.SerializerMethodField()

    # Optional fields (may not exist as real model fields). Read from attrs or condition_data.
    original_price = serializers.SerializerMethodField()
    years_used = serializers.SerializerMethodField()
    grade_label = serializers.SerializerMethodField()
    grade_score = serializers.SerializerMethodField()
    defects = serializers.SerializerMethodField()

    estimated_min = serializers.SerializerMethodField()
    estimated_max = serializers.SerializerMethodField()
    estimated_mid = serializers.SerializerMethodField()
    market_tag = serializers.SerializerMethodField()
    diff_pct = serializers.SerializerMethodField()
    value_score = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "seller_id",
            "seller_name",
            "seller_address",
            "category_id",
            "device_model_id",
            "title",
            "description",
            "selling_price",
            "original_price",
            "years_used",
            "grade_label",
            "grade_score",
            "defects",
            "estimated_min",
            "estimated_max",
            "estimated_mid",
            "market_tag",
            "diff_pct",
            "value_score",
            "status",
            "view_count",
            "favorite_count",
            "main_image",
            "created_at",
        ]

    def get_main_image(self, obj):
        img = obj.images.order_by("sort_order", "id").first()
        if not img:
            return None
        # 返回相对路径，交由前端按 /media/products/<name> 展示
        return f"/media/products/{img.image_name}"

    def get_created_at(self, obj):
        dt = getattr(obj, "created_at", None)
        if not dt:
            return None
        # 统一用北京时间（Asia/Shanghai），24小时制
        try:
            bj = ZoneInfo("Asia/Shanghai")
        except Exception:
            bj = None

        try:
            dt_local = timezone.localtime(dt, bj) if bj else timezone.localtime(dt)
        except Exception:
            # 若 dt 是 naive，先当作当前时区处理
            dt_local = dt

        return dt_local.strftime("%Y-%m-%d %H:%M:%S")

    def get_seller_id(self, obj):
        # Product.seller is expected
        return getattr(obj, "seller_id", None)

    def get_seller_name(self, obj):
        seller = getattr(obj, "seller", None)
        if not seller:
            return None
        # Prefer nickname, then username
        nick = getattr(seller, "nickname", None)
        if nick:
            return nick
        return getattr(seller, "username", None)

    def get_seller_address(self, obj):
        seller = getattr(obj, "seller", None)
        if not seller:
            return None
        return getattr(seller, "address", None)

    def get_category_id(self, obj):
        # Prefer explicit field; fall back via device_model->brand->category
        cid = getattr(obj, "category_id", None)
        if cid is not None:
            return cid
        try:
            return obj.device_model.brand.category_id
        except Exception:
            return None

    def get_device_model_id(self, obj):
        return getattr(obj, "device_model_id", None)

    def _cond(self, obj):
        cd = getattr(obj, "condition_data", None)
        return cd if isinstance(cd, dict) else {}

    def get_original_price(self, obj):
        v = getattr(obj, "original_price", None)
        if v is not None:
            return v
        return self._cond(obj).get("original_price")

    def get_years_used(self, obj):
        v = getattr(obj, "years_used", None)
        if v is not None:
            return v
        return self._cond(obj).get("years_used")

    def get_grade_label(self, obj):
        v = getattr(obj, "grade_label", None)
        if v is not None:
            return v
        return self._cond(obj).get("grade_label")

    def get_grade_score(self, obj):
        v = getattr(obj, "grade_score", None)
        if v is not None:
            return v
        return self._cond(obj).get("grade_score")

    def get_defects(self, obj):
        v = getattr(obj, "defects", None)
        if v is not None:
            return v
        return self._cond(obj).get("defects")

    def get_estimated_min(self, obj):
        v = getattr(obj, "estimated_min", None)
        if v is not None:
            return v
        return self._cond(obj).get("estimated_min")

    def get_estimated_max(self, obj):
        v = getattr(obj, "estimated_max", None)
        if v is not None:
            return v
        return self._cond(obj).get("estimated_max")

    def get_estimated_mid(self, obj):
        v = getattr(obj, "estimated_mid", None)
        if v is not None:
            return v
        return self._cond(obj).get("estimated_mid")

    def get_market_tag(self, obj):
        v = getattr(obj, "market_tag", None)
        if v is not None:
            return v
        return self._cond(obj).get("market_tag")

    def get_diff_pct(self, obj):
        v = getattr(obj, "diff_pct", None)
        if v is not None:
            return v
        return self._cond(obj).get("diff_pct")

    def get_value_score(self, obj):
        v = getattr(obj, "value_score", None)
        if v is not None:
            return v
        return self._cond(obj).get("value_score")