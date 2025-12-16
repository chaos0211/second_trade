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
    OrderDetailSerializer,
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

    def get_serializer_class(self):
        # 列表/详情返回订单+商品摘要信息，便于前端展示
        if self.action in {"list", "retrieve", "buy", "sell"}:
            return OrderDetailSerializer
        return OrderSerializer

    def get_queryset(self):
        """订单可见性（不依赖前端 role 参数）：

        - 默认 list / buy：buyer == 当前用户
        - sell / ship：product.seller == 当前用户
        """
        user = self.request.user
        action = getattr(self, "action", None)

        qs = Order.objects.select_related("product", "buyer", "product__seller")

        if action in {"sell", "ship"}:
            return qs.filter(product__seller=user)

        # 默认：买家订单
        return qs.filter(buyer=user)

    def _ensure_buyer(self, order: Order):
        if order.buyer_id != self.request.user.id:
            raise PermissionError("not buyer")

    def _ensure_seller(self, order: Order):
        if getattr(order, "product_id", None) is None or order.product.seller_id != self.request.user.id:
            raise PermissionError("not seller")

    def _is_terminal(self, status: str) -> bool:
        return status in {"completed", "refunded"}

    def _status_view(self, status: str, perspective: str) -> str:
        """Return UI-friendly status label depending on perspective.

        perspective: 'buyer' | 'seller'
        """
        # Canonical states:
        # pending_payment -> buyer: 待付款, seller: 待买家付款
        # pending_shipment -> buyer: 待发货, seller: 待发货
        # shipped -> buyer: 待收货, seller: 已发货
        # completed -> 已完成
        # refunded -> 已取消
        if status == "pending_payment":
            return "待付款" if perspective == "buyer" else "待买家付款"
        if status == "pending_shipment":
            return "待发货"
        if status == "shipped":
            return "待收货" if perspective == "buyer" else "已发货"
        if status == "completed":
            return "已完成"
        if status == "refunded":
            return "已取消"
        # Backward compat
        if status == "created":
            return "待付款" if perspective == "buyer" else "待买家付款"
        if status == "pending_receipt":
            return "待收货" if perspective == "buyer" else "已发货"
        if status == "received":
            return "已完成"
        return "未知状态"

    def _attach_status_view(self, payload, perspective: str):
        """Attach status_view to serializer output. Works for list/dict."""
        if payload is None:
            return payload
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    st = item.get("status")
                    item["status_view"] = self._status_view(st, perspective)
            return payload
        if isinstance(payload, dict):
            # paginated shape
            if "results" in payload and isinstance(payload.get("results"), list):
                for item in payload["results"]:
                    if isinstance(item, dict):
                        st = item.get("status")
                        item["status_view"] = self._status_view(st, perspective)
                return payload
            st = payload.get("status")
            payload["status_view"] = self._status_view(st, perspective)
            return payload
        return payload

    @action(detail=False, methods=["post"])
    def create_trade(self, request):
        """
        创建交易订单
        """
        product_id = request.data.get("product_id")
        try:
            product_id = int(product_id)
            order = TradeService.create_order(request.user, product_id)
            # 初始为待付款
            if getattr(order, "status", None) in (None, "", "created"):
                order.status = "pending_payment"
                order.save(update_fields=["status"])
            return Response(
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "status": order.status or "pending_payment",
                    "status_view": self._status_view(order.status or "pending_payment", "buyer"),
                    "product_id": product_id,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=["get"])
    def buy(self, request):
        """买家订单列表：我买的"""
        qs = Order.objects.select_related("product", "buyer", "product__seller").filter(buyer=request.user).order_by("-id")
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            resp = self.get_paginated_response(ser.data)
            self._attach_status_view(resp.data, "buyer")
            return resp
        ser = self.get_serializer(qs, many=True)
        data = ser.data
        self._attach_status_view(data, "buyer")
        return Response(data)

    @action(detail=False, methods=["get"])
    def sell(self, request):
        """卖家订单列表：我卖出的（通过订单关联商品联查卖家）"""
        qs = Order.objects.select_related("product", "buyer", "product__seller").filter(product__seller=request.user).order_by("-id")
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            resp = self.get_paginated_response(ser.data)
            self._attach_status_view(resp.data, "seller")
            return resp
        ser = self.get_serializer(qs, many=True)
        data = ser.data
        self._attach_status_view(data, "seller")
        return Response(data)

    @action(detail=True, methods=["post"])
    def confirm_receipt(self, request, pk=None):
        """买家确认收货 -> 状态：completed（完成）"""
        try:
            order = self.get_object()
            self._ensure_buyer(order)

            if self._is_terminal(order.status):
                return Response({"error": "order is terminal"}, status=400)

            # 仅允许在已发货阶段确认收货
            if order.status not in {"shipped"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "completed"
            order.save(update_fields=["status"])
            return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})
        except PermissionError:
            return Response({"error": "permission denied"}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """买家付款 -> 状态：pending_shipment（待发货）"""
        try:
            order = self.get_object()
            self._ensure_buyer(order)

            if self._is_terminal(order.status):
                return Response({"error": "order is terminal"}, status=400)

            # 仅允许从待付款进入付款
            if order.status not in {"pending_payment", "created"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "pending_shipment"
            order.save(update_fields=["status"])
            return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})
        except PermissionError:
            return Response({"error": "permission denied"}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def cancel_payment(self, request, pk=None):
        """买家取消付款 -> 状态：refunded（已退款/取消），终态不可继续操作"""
        try:
            order = self.get_object()
            self._ensure_buyer(order)

            if self._is_terminal(order.status):
                return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})

            # 允许在待付款阶段取消
            if order.status not in {"created", "pending_payment"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "refunded"
            order.save(update_fields=["status"])
            return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})
        except PermissionError:
            return Response({"error": "permission denied"}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        """卖家发货 -> 状态：shipped（待收货）"""
        try:
            order = self.get_object()
            self._ensure_seller(order)

            if self._is_terminal(order.status):
                return Response({"error": "order is terminal"}, status=400)

            # 仅允许待发货的订单发货
            if order.status not in {"pending_shipment"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "shipped"
            order.save(update_fields=["status"])
            return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "seller")})
        except PermissionError:
            return Response({"error": "permission denied"}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """买家退货退款 -> 状态：refunded（已退款/取消），终态不可继续操作"""
        try:
            order = self.get_object()
            self._ensure_buyer(order)

            if self._is_terminal(order.status):
                return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})

            # 仅允许在已发货阶段退款/取消收货
            if order.status not in {"shipped"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "refunded"
            order.save(update_fields=["status"])
            return Response({"order_id": order.id, "status": order.status, "status_view": self._status_view(order.status, "buyer")})
        except PermissionError:
            return Response({"error": "permission denied"}, status=403)
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