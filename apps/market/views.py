from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .services import ValuationEngine, TradeService
from .models import Category, DeviceModel, Product, Order
from .serializers import (
    ValuationRequestSerializer,
    ProductCreateSerializer,
    ProductListSerializer,
    OrderSerializer,
    CategorySerializer,
    DeviceModelSerializer,
)


class ValuationAPI(APIView):
    """
    智能估价接口
    """

    def post(self, request):
        serializer = ValuationRequestSerializer(data=request.data)
        if serializer.is_valid():
            price = ValuationEngine.calculate_price(
                serializer.validated_data["device_model_id"],
                serializer.validated_data["choice_ids"],
            )
            return Response(
                {
                    "estimated_price": str(price),  # 转成字符串便于前端处理
                    "currency": "CNY",
                    "message": "估价成功，基于动态市场策略",
                }
            )
        return Response(serializer.errors, status=400)


class ProductViewSet(ModelViewSet):
    """
    商品上架与浏览接口
    """

    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProductListSerializer
        return ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        上架时自动关联卖家用户。
        estimated_price 在真实业务中建议从前端传入（由 ValuationAPI 估价后缓存），
        这里先用 0 作为占位。
        """
        serializer.save(
            seller=self.request.user,
            status="on_sale",
            estimated_price=0,
        )

    def get_queryset(self):
        """同一接口支持两种场景：

        1) 市场大厅：不传 seller_id -> 返回所有上架商品
        2) 卖家页：传 seller_id -> 仅返回该卖家的上架商品

        GET /api/market/products/                # 市场大厅
        GET /api/market/products/?seller_id=123  # 卖家上架中商品
        """
        qs = Product.objects.filter(status="on_sale")

        seller_id = self.request.query_params.get("seller_id")
        if seller_id:
            try:
                sid = int(seller_id)
                qs = qs.filter(seller_id=sid)
            except Exception:
                return Product.objects.none()

        return qs


class OrderViewSet(ModelViewSet):
    """
    订单接口
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回当前用户作为买家的订单
        return Order.objects.filter(buyer=self.request.user)

    @action(detail=False, methods=["post"])
    def create_trade(self, request):
        """
        创建交易订单
        """
        product_id = request.data.get("product_id")
        try:
            product_id = int(product_id)
            order = TradeService.create_order(request.user, product_id)
            return Response(
                {
                    "order_no": order.order_no,
                    "status": "created",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def confirm_receipt(self, request, pk=None):
        """
        买家确认收货，完成交易闭环
        """
        try:
            TradeService.complete_order(pk, request.user)
            return Response(
                {
                    "status": "success",
                    "message": "交易完成，信用分已更新",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class CategoryViewSet(ModelViewSet):
    """类目列表（market_category）"""

    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["get"]


class DeviceModelViewSet(ModelViewSet):
    """型号列表（market_devicemodel）

    兼容前端传 brand_id=category_id：
    - /api/market/device-models/?brand_id=<category_id>
      -> 过滤 DeviceModel.brand.category_id == brand_id
    """

    queryset = DeviceModel.objects.select_related("brand", "brand__category").all().order_by("id")
    serializer_class = DeviceModelSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["get"]

    def get_queryset(self):
        qs = super().get_queryset()
        brand_id = self.request.query_params.get("brand_id")
        category_id = self.request.query_params.get("category_id")

        # 兼容：brand_id 传的是 category_id
        if brand_id:
            try:
                cid = int(brand_id)
                return qs.filter(brand__category_id=cid)
            except Exception:
                return qs.none()

        if category_id:
            try:
                cid = int(category_id)
                return qs.filter(brand__category_id=cid)
            except Exception:
                return qs.none()

        return qs