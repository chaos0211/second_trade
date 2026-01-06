from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import FieldError

from .services import ValuationEngine, TradeService
from apps.accounts.services.credit import apply_credit_event, can_trade
from .models import Category, DeviceModel, Product, Order, Brand
from .serializers import (
    ValuationRequestSerializer,
    ProductCreateSerializer,
    ProductListSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    CategorySerializer,
    DeviceModelSerializer,
    BrandSerializer,
)


class ValuationAPI(APIView):
    """智能估价接口"""

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
    """商品上架与浏览接口"""

    queryset = Product.objects.select_related(
        "seller",
        "device_model",
        "device_model__brand",
        "device_model__brand__category",
    ).all()
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProductListSerializer
        return ProductCreateSerializer

    def retrieve(self, request, *args, **kwargs):
        """商品详情：在原有序列化结果基础上，额外返回联查得到的类目/品牌/型号信息。

        目的：前端 getProductDetail() 不需要再额外请求 category/device-model 等接口。
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = dict(serializer.data)

        # device_model -> brand -> category
        dm = getattr(instance, "device_model", None)
        brand = getattr(dm, "brand", None) if dm is not None else None
        category = getattr(brand, "category", None) if brand is not None else None

        # 保留旧字段（若 serializer 已返回，则不覆盖）
        # 同时补充更直观的 *_name 字段供前端直接展示
        if "device_model_id" not in data and dm is not None:
            data["device_model_id"] = dm.id
        data["device_model_name"] = getattr(dm, "name", None)

        if "brand_id" not in data and brand is not None:
            data["brand_id"] = brand.id
        data["brand_name"] = getattr(brand, "name", None)

        if "category_id" not in data and category is not None:
            data["category_id"] = category.id
        data["category_name"] = getattr(category, "name", None)

        # 参考价（DeviceModel.msrp/base_price）给详情页“商品参考”用
        # 字段名不强绑定，尽量兼容已有模型字段
        if dm is not None:
            if "msrp_price" not in data:
                data["msrp_price"] = getattr(dm, "msrp_price", None)
            if data.get("msrp_price") in (None, "") and "base_price" not in data:
                data["base_price"] = getattr(dm, "base_price", None)

        return Response(data)

    def perform_create(self, serializer):
        """上架时自动关联卖家用户，并进行信用分门槛校验。"""
        # 信用分 < 60：禁止买卖
        if not can_trade(getattr(self.request.user, "credit_score", 0)):
            return Response({"error": "信用分过低，无法上架"}, status=403)

        serializer.save(
            seller=self.request.user,
            status="on_sale",
            estimated_price=0,
        )

    def get_queryset(self):
        """同一接口支持两种场景：

        1) 市场大厅：不传 seller_id -> 返回所有上架商品
        2) 卖家页：传 seller_id -> 仅返回该卖家的上架商品

        额外支持：
        - category_id：按类目筛选上架商品

        GET /api/market/products/                          # 市场大厅
        GET /api/market/products/?seller_id=123            # 卖家上架中商品
        GET /api/market/products/?category_id=15           # 指定类目
        GET /api/market/products/?seller_id=123&category_id=15
        """
        qs = Product.objects.filter(status="on_sale")

        # filter by category_id (Product 本身不存 category_id，需要通过 device_model -> brand -> category 过滤)
        category_id = self.request.query_params.get("category_id")
        if category_id is not None and str(category_id).strip() != "":
            try:
                cid = int(str(category_id).strip())
                # 最稳：按关联链过滤
                qs = qs.filter(device_model__brand__category_id=cid)
            except Exception:
                # ignore invalid category_id instead of returning empty
                pass

        # filter by seller_id
        seller_id = self.request.query_params.get("seller_id")
        if seller_id is not None and str(seller_id).strip() != "":
            try:
                sid = int(str(seller_id).strip())
                try:
                    qs = qs.filter(seller_id=sid)
                except FieldError:
                    qs = qs.filter(seller__id=sid)
            except Exception:
                # ignore invalid seller_id instead of returning empty
                pass

        return qs.distinct()


class OrderViewSet(ModelViewSet):
    """订单接口"""

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
        """创建交易订单"""
        # 信用分 < 60：禁止买卖
        if not can_trade(getattr(request.user, "credit_score", 0)):
            return Response({"error": "信用分过低，无法购买"}, status=403)

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
        qs = (
            Order.objects.select_related("product", "buyer", "product__seller")
            .filter(buyer=request.user)
            .order_by("-id")
        )
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
        qs = (
            Order.objects.select_related("product", "buyer", "product__seller")
            .filter(product__seller=request.user)
            .order_by("-id")
        )
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

            if order.status not in {"shipped"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "completed"
            order.save(update_fields=["status"])

            # 订单完成：买家 +3，卖家 +3（幂等）
            try:
                apply_credit_event(
                    user=request.user,
                    event_type="order_completed",
                    ref_type="order",
                    ref_id=str(order.id),
                )
                apply_credit_event(
                    user=order.product.seller,
                    event_type="order_completed",
                    ref_type="order",
                    ref_id=str(order.id),
                )
            except Exception:
                # 积分不影响主流程
                pass

            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "status_view": self._status_view(order.status, "buyer"),
                }
            )
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

            if order.status not in {"pending_payment", "created"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "pending_shipment"
            order.save(update_fields=["status"])
            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "status_view": self._status_view(order.status, "buyer"),
                }
            )
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
                return Response(
                    {
                        "order_id": order.id,
                        "status": order.status,
                        "status_view": self._status_view(order.status, "buyer"),
                    }
                )

            if order.status not in {"created", "pending_payment"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "refunded"
            order.save(update_fields=["status"])

            # 取消付款：取消者（买家） -3（幂等）
            try:
                apply_credit_event(
                    user=request.user,
                    event_type="payment_cancelled",
                    ref_type="order",
                    ref_id=str(order.id),
                )
            except Exception:
                pass

            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "status_view": self._status_view(order.status, "buyer"),
                }
            )
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

            if order.status not in {"pending_shipment"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "shipped"
            order.save(update_fields=["status"])
            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "status_view": self._status_view(order.status, "seller"),
                }
            )
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
                return Response(
                    {
                        "order_id": order.id,
                        "status": order.status,
                        "status_view": self._status_view(order.status, "buyer"),
                    }
                )

            if order.status not in {"shipped"}:
                return Response({"error": "invalid status"}, status=400)

            order.status = "refunded"
            order.save(update_fields=["status"])

            # 退货退款：买家 -3，卖家 -1（幂等）
            try:
                apply_credit_event(
                    user=request.user,
                    event_type="order_refunded",
                    party="buyer",
                    ref_type="order",
                    ref_id=str(order.id),
                )
                apply_credit_event(
                    user=order.product.seller,
                    event_type="order_refunded",
                    party="seller",
                    ref_type="order",
                    ref_id=str(order.id),
                )
            except Exception:
                pass

            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "status_view": self._status_view(order.status, "buyer"),
                }
            )
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


class BrandViewSet(ModelViewSet):
    """品牌列表（market_brand）

    GET /api/market/brands/
    GET /api/market/brands/?category_id=<id>
    """

    queryset = Brand.objects.select_related("category").all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["get"]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get("category_id")
        if category_id:
            try:
                cid = int(category_id)
                qs = qs.filter(category_id=cid)
            except Exception:
                return qs.none()
        return qs


class DeviceModelViewSet(ModelViewSet):
    """型号列表（market_devicemodel）

    支持按类目与品牌过滤：
    - /api/market/device-models/?category_id=<cid>&brand_id=<bid>
    - /api/market/device-models/?category_id=<cid>
    - /api/market/device-models/?brand_id=<bid>

    兼容历史用法（极少数旧前端把 category_id 误传到 brand_id）：
    - 当仅传 brand_id 且该 brand_id 在 Brand 表中不存在时，按 category_id 处理。
    """

    queryset = DeviceModel.objects.select_related("brand", "brand__category").all().order_by("id")
    serializer_class = DeviceModelSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["get"]

    def get_queryset(self):
        qs = super().get_queryset()

        brand_id = self.request.query_params.get("brand_id")
        category_id = self.request.query_params.get("category_id")

        if category_id:
            try:
                qs = qs.filter(brand__category_id=int(category_id))
            except ValueError:
                return qs.none()

        if brand_id:
            try:
                qs = qs.filter(brand_id=int(brand_id))
            except ValueError:
                return qs.none()

        return qs

    @action(detail=False, methods=["get"], url_path="reference")
    def reference(self, request):
        """参考机型信息（用于商品详情页右侧“商品参考”扩展页）。

        用法：
        - GET /api/market/device-models/reference/?category_id=<cid>&device_model_id=<dm_id>

        返回字段：name、brand_id、image_url、msrp_price
        """
        category_id = request.query_params.get("category_id")
        device_model_id = request.query_params.get("device_model_id")

        if not category_id or not device_model_id:
            return Response({"error": "category_id and device_model_id are required"}, status=400)

        try:
            cid = int(str(category_id).strip())
            dm_id = int(str(device_model_id).strip())
        except Exception:
            return Response({"error": "invalid category_id or device_model_id"}, status=400)

        qs = (
            DeviceModel.objects.select_related("brand", "brand__category")
            .filter(id=dm_id, brand__category_id=cid)
        )

        dm = qs.first()
        if dm is None:
            return Response({"error": "not found"}, status=404)

        payload = {
            "id": dm.id,
            "name": getattr(dm, "name", None),
            "brand_id": getattr(dm, "brand_id", None),
            "image_url": getattr(dm, "image_url", None),
            "msrp_price": getattr(dm, "msrp_price", None),
        }
        return Response(payload)