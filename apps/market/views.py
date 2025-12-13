from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .services import ValuationEngine, TradeService
from .models import Product, Order
from .serializers import (
    ValuationRequestSerializer,
    ProductCreateSerializer,
    OrderSerializer,
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
        # 只展示上架中的商品
        return Product.objects.filter(status="on_sale")


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
