from rest_framework import serializers
from decimal import Decimal

from django.utils import timezone
from zoneinfo import ZoneInfo

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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "code"]


class DeviceModelSerializer(serializers.ModelSerializer):
    # 前端用 brand_id 对接 category_id
    brand_id = serializers.IntegerField(source="brand.category_id", read_only=True)

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

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "selling_price",
            "estimated_price",
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