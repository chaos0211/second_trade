from decimal import Decimal
import uuid

from django.db import transaction
from django.contrib.auth import get_user_model

from .models import DeviceModel, ValuationChoice, Product, Order

User = get_user_model()


class ValuationEngine:
    """
    轻量化智能估价引擎
    """

    @staticmethod
    def calculate_price(device_model_id, choice_ids):
        """
        核心算法：基准价 * (1 - 总折旧率) * 市场波动系数
        """
        try:
            device = DeviceModel.objects.get(id=device_model_id)
            base_price = device.base_price

            total_depreciation = 0.0

            # 获取所有用户选择的选项
            choices = ValuationChoice.objects.filter(id__in=choice_ids)

            for choice in choices:
                # 累加折旧率 (例如：屏幕划痕-5% + 电池损耗-10% = -15%)
                total_depreciation += choice.depreciation_rate

            # 防止折旧超过100%
            if total_depreciation > 0.9:
                total_depreciation = 0.9

            # 动态策略：简单的市场波动模拟 (实际项目中可接入爬虫数据或Redis缓存)
            market_factor = Decimal("1.0")
            # 这里可以扩展更多逻辑...

            final_price = base_price * (Decimal("1.0") - Decimal(str(total_depreciation))) * market_factor

            # 最低回收价保护
            return max(final_price, Decimal("50.00"))

        except DeviceModel.DoesNotExist:
            return Decimal("0.00")


class TradeService:
    """
    交易闭环服务
    """

    @staticmethod
    @transaction.atomic
    def create_order(user, product_id):
        product = Product.objects.select_for_update().get(id=product_id)

        if product.status != "on_sale":
            raise ValueError("商品不可购买")

        if product.seller == user:
            raise ValueError("不能购买自己的商品")

        # 锁定商品
        product.status = "locked"
        product.save()

        order = Order.objects.create(
            order_no=str(uuid.uuid4()).replace("-", ""),
            buyer=user,
            product=product,
            amount=product.selling_price,
            status="pending_payment",
        )
        return order

    @staticmethod
    @transaction.atomic
    def complete_order(order_id, user):
        """
        完成订单：解冻资金，打款给卖家，增加信用分
        """
        order = Order.objects.select_for_update().get(id=order_id)

        if order.buyer != user:
            raise PermissionError("无权操作")

        if order.status != "shipped":
            raise ValueError("订单状态不正确")

        # 1. 更新订单状态
        order.status = "completed"
        order.save()

        product = order.product
        product.status = "sold"
        product.save()

        # 2. 资金划转 (简化版，实际应调用支付网关分账接口)
        seller = product.seller
        seller.balance += order.amount
        seller.save()

        # 3. 信用积分体系：交易完成，双方加分
        seller.update_credit(10)
        user.update_credit(10)

        return order