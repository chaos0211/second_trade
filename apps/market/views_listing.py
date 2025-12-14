import os
import uuid
import hashlib
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .ai_service import AIService
from .pricing import estimate_range, compare_price, value_score_from_diff
from .models import Category, DeviceModel, Product, ProductImage, ConditionGrade
from .serializers import (
    DraftInitSerializer, UploadImageSerializer,
    EstimateSerializer, PublishSerializer
)

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}
MAX_IMAGES = 4

def ensure_media_dir():
    if not hasattr(settings, "MEDIA_ROOT") or not settings.MEDIA_ROOT:
        raise RuntimeError("MEDIA_ROOT 未配置")
    folder = os.path.join(settings.MEDIA_ROOT, "products")
    os.makedirs(folder, exist_ok=True)
    return folder

def encrypt_filename(original_name: str) -> str:
    ext = os.path.splitext(original_name)[1].lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext not in ALLOWED_EXT:
        raise ValueError("只支持 jpg/png")
    raw = f"{uuid.uuid4()}-{timezone.now().timestamp()}".encode("utf-8")
    name = hashlib.sha256(raw).hexdigest()[:32] + ".jpg"  # 统一落盘 jpg
    return name, ext

class DraftInitAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = DraftInitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        draft_key = uuid.uuid4().hex
        # 前端后续都带这个 draft_key
        return Response({
            "draft_key": draft_key,
            "meta": ser.validated_data
        })

class DraftUploadImagesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, draft_key: str):
        folder = ensure_media_dir()

        # 数量限制
        exist = ProductImage.objects.filter(uploaded_by=request.user, draft_key=draft_key, product__isnull=True).count()
        if exist >= MAX_IMAGES:
            return Response({"detail": "最多上传4张"}, status=400)

        ser = UploadImageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        f = ser.validated_data["image"]

        image_name, ext = encrypt_filename(getattr(f, "name", "upload.jpg"))

        # 保存文件（统一转 jpg：这里先直接原样写入，后续你要真转jpg再加 Pillow）
        path = os.path.join(folder, image_name)
        with open(path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        is_main = (exist == 0)
        img = ProductImage.objects.create(
            uploaded_by=request.user,
            draft_key=draft_key,
            image_name=image_name,
            original_name=getattr(f, "name", ""),
            size_bytes=getattr(f, "size", 0) or 0,
            is_main=is_main,
            sort_order=0 if is_main else exist,
        )

        return Response({
            "id": img.id,
            "image_name": img.image_name,
            "is_main": img.is_main,
            "sort_order": img.sort_order,
        }, status=201)

class DraftAnalyzeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, draft_key: str):
        imgs = ProductImage.objects.filter(
            uploaded_by=request.user, draft_key=draft_key, product__isnull=True
        ).order_by("sort_order","id")
        if not imgs.exists():
            return Response({"detail": "请先上传图片"}, status=400)

        main_img = imgs.first()
        image_path = os.path.join(settings.MEDIA_ROOT, "products", main_img.image_name)

        result = AIService.analyze_image(image_path)

        # 返回：瑕疵文本 + 成色标签
        return Response({
            "main_image": main_img.image_name,
            "grade_label": result["label"],
            "grade_score": result["score"],
            "defects": result["defects"],
        })

class DraftEstimateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, draft_key: str):
        ser = EstimateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 步骤1的 meta 你现在前端传一次即可（建议前端把 meta 存起来，这里直接从 request 带）
        category_id = int(request.data.get("category_id"))
        years_used = float(request.data.get("years_used"))
        original_price = Decimal(str(request.data.get("original_price")))

        category = Category.objects.get(id=category_id)
        category_code = category.code or "other"

        # grade_factor：优先 grade_id，其次 grade_label 匹配 ConditionGrade
        grade_factor = Decimal("0.75")
        grade_label = ser.validated_data.get("grade_label", "")
        grade_id = ser.validated_data.get("grade_id")

        if grade_id:
            g = ConditionGrade.objects.get(id=grade_id)
            grade_label = g.label
            grade_factor = g.factor
        elif grade_label:
            g = ConditionGrade.objects.filter(category=category, label=grade_label).first()
            if g:
                grade_factor = g.factor

        # 瑕疵扣减：先用“假AI defects 数量”简单映射（后续再替换成 DefectSeverity 的权重）
        defects = request.data.get("defects") or []
        defects_count = len(defects)
        defect_penalty = Decimal("0.00")
        if defects_count == 0:
            defect_penalty = Decimal("0.02")
        elif defects_count == 1:
            defect_penalty = Decimal("0.08")
        else:
            defect_penalty = Decimal("0.15")

        r = estimate_range(
            original_price=original_price,
            years_used=years_used,
            grade_factor=grade_factor,
            defect_penalty=defect_penalty,
            category_code=category_code,
        )

        return Response({
            "category": {"id": category.id, "name": category.name, "code": category.code},
            "grade": {"label": grade_label, "factor": str(grade_factor)},
            "estimated_min": str(r["estimated_min"]),
            "estimated_max": str(r["estimated_max"]),
            "estimated_mid": str(r["estimated_mid"]),
            "volatility": r["volatility"],
            "defect_penalty": r["defect_penalty"],
        })

class DraftPublishAPI(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, draft_key: str):
        ser = PublishSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 必须带步骤1 meta + 步骤3估价结果
        category_id = int(request.data.get("category_id"))
        device_model_id = request.data.get("device_model_id")
        years_used = float(request.data.get("years_used"))
        original_price = Decimal(str(request.data.get("original_price")))
        grade_label = request.data.get("grade_label", "")
        defects = request.data.get("defects") or []

        category = Category.objects.get(id=category_id)
        device_model = None
        if device_model_id:
            device_model = DeviceModel.objects.get(id=int(device_model_id))
        else:
            # 没选型号也要能上架：临时用一个“占位型号”策略（建议你强制选择型号更好）
            return Response({"detail": "请先选择商品型号"}, status=400)

        # 估价：复用 DraftEstimateAPI 的逻辑（此处简化重复一次）
        g = ConditionGrade.objects.filter(category=category, label=grade_label).first()
        grade_factor = g.factor if g else Decimal("0.75")

        defect_penalty = Decimal("0.02") if len(defects) == 0 else (Decimal("0.08") if len(defects)==1 else Decimal("0.15"))
        r = estimate_range(original_price, years_used, grade_factor, defect_penalty, category.code or "other")

        selling_price = ser.validated_data["selling_price"]
        diff_pct, market_tag = compare_price(Decimal(str(selling_price)), r["estimated_min"], r["estimated_max"])
        value_score = value_score_from_diff(diff_pct)

        product = Product.objects.create(
            seller=request.user,
            device_model=device_model,
            title=ser.validated_data["title"],
            description=ser.validated_data["description"],
            estimated_price=r["estimated_mid"],
            selling_price=selling_price,
            status="on_sale",
            condition_data={
                "category_id": category_id,
                "years_used": years_used,
                "original_price": str(original_price),
                "grade_label": grade_label,
                "defects": defects,
                "market_tag": market_tag,
                "diff_pct": diff_pct,
                "value_score": value_score,
            },
            # 先简单映射：成色字段你后面想改成 grade_label 就行
            quality_grade="B",
        )

        # 绑定图片：把 draft_key 下图片 product 赋值，并清空 draft_key
        imgs = ProductImage.objects.filter(uploaded_by=request.user, draft_key=draft_key, product__isnull=True).order_by("sort_order","id")
        if not imgs.exists():
            return Response({"detail": "没有可绑定的图片"}, status=400)

        for img in imgs:
            img.product = product
            img.draft_key = ""
            img.save(update_fields=["product","draft_key"])

        return Response({
            "product_id": product.id,
            "estimated_min": str(r["estimated_min"]),
            "estimated_max": str(r["estimated_max"]),
            "estimated_mid": str(r["estimated_mid"]),
            "market_tag": market_tag,
            "diff_pct": diff_pct,
            "value_score": value_score,
        }, status=201)