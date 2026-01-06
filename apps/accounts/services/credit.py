from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from django.conf import settings
from django.db import IntegrityError, transaction


# CreditEvent 可能在 market.models（你当前项目里是订单域）
# 也可能后续迁移到 accounts.models；这里做兼容导入。
try:  # pragma: no cover
    from apps.accounts.models import CreditEvent  # type: ignore
except Exception:  # pragma: no cover
    from apps.market.models import CreditEvent  # type: ignore


MAX_CREDIT_SCORE = 120


@dataclass(frozen=True)
class CreditResult:
    created: bool
    event_id: Optional[int]
    delta: int
    score_before: int
    score_after: int
    level: str


def credit_level(score: int) -> str:
    """
    评分等级：
    - < 60：极差（不可买卖）
    - 60-80：差
    - 81-100：一般
    - 101-120：优秀
    """
    if score < 60:
        return "极差"
    if 60 <= score <= 80:
        return "差"
    if 81 <= score <= 100:
        return "一般"
    return "优秀"


def can_trade(score: int) -> bool:
    return score >= 60


def _normalize_event_type(event_type: str) -> str:
    et = (event_type or "").strip()
    # 允许一些别名
    alias = {
        "completed": "order_completed",
        "order_complete": "order_completed",
        "order_completed": "order_completed",

        "cancel": "payment_cancelled",
        "cancel_payment": "payment_cancelled",
        "payment_cancelled": "payment_cancelled",

        "refund": "order_refunded",
        "refunded": "order_refunded",
        "order_refunded": "order_refunded",

        "manual": "manual_adjust",
        "manual_adjust": "manual_adjust",
    }
    return alias.get(et, et)


def _compute_delta(event_type: str, party: Optional[str] = None, manual_delta: Optional[int] = None) -> int:
    """按你当前约束返回 delta。"""
    et = _normalize_event_type(event_type)

    if et == "order_completed":
        return 3

    if et == "payment_cancelled":
        # 取消订单/取消支付：取消者 -3
        return -3

    if et == "order_refunded":
        # 退货：买家 -3，卖家 -1
        p = (party or "").strip().lower()
        if p in ("buyer", "b"):
            return -3
        if p in ("seller", "s"):
            return -1
        raise ValueError("order_refunded requires party='buyer' or party='seller'")

    if et == "manual_adjust":
        if manual_delta is None:
            raise ValueError("manual_adjust requires manual_delta")
        return int(manual_delta)

    raise ValueError(f"unsupported event_type: {event_type}")


def apply_credit_event(
    *,
    user,
    event_type: str,
    ref_type: str = "",
    ref_id: str = "",
    reason: str = "",
    party: Optional[str] = None,
    manual_delta: Optional[int] = None,
) -> CreditResult:
    """写入积分事件并更新 user.credit_score。

    规则（按你当前定义）：
    - 订单完成：+3
    - 取消订单（取消者）：-3
    - 退货：买家 -3，卖家 -1
    - 120 封顶

    幂等：同一 (user, event_type, ref_type, ref_id) 只记一次。
    """

    et = _normalize_event_type(event_type)
    delta = _compute_delta(et, party=party, manual_delta=manual_delta)

    # 兼容：ref_id 统一转字符串，避免 UniqueConstraint 因类型差异导致重复
    ref_type = (ref_type or "").strip()
    ref_id = str(ref_id or "").strip()

    UserModel = type(user)

    with transaction.atomic():
        # 锁定用户行，避免并发加分导致覆盖
        locked_user = UserModel.objects.select_for_update().get(pk=user.pk)
        score_before = int(getattr(locked_user, "credit_score", 0) or 0)

        # 先查是否已存在（幂等）
        existing = CreditEvent.objects.filter(
            user_id=locked_user.pk,
            event_type=et,
            ref_type=ref_type,
            ref_id=ref_id,
        ).first()
        if existing is not None:
            score_after = int(getattr(locked_user, "credit_score", 0) or 0)
            return CreditResult(
                created=False,
                event_id=existing.id,
                delta=int(existing.delta or 0),
                score_before=score_before,
                score_after=score_after,
                level=credit_level(score_after),
            )

        # 计算封顶
        proposed = score_before + int(delta)
        score_after = min(MAX_CREDIT_SCORE, proposed)

        # 可选：不允许出现负数（如果你希望允许负数，把下面这行删掉）
        if score_after < 0:
            score_after = 0

        # 写入事件 + 更新用户积分
        evt = CreditEvent.objects.create(
            user=locked_user,
            event_type=et,
            delta=int(delta),
            score_after=score_after,
            ref_type=ref_type,
            ref_id=ref_id,
            reason=(reason or "").strip(),
        )

        setattr(locked_user, "credit_score", score_after)
        locked_user.save(update_fields=["credit_score"])  # type: ignore[arg-type]

        return CreditResult(
            created=True,
            event_id=evt.id,
            delta=int(delta),
            score_before=score_before,
            score_after=score_after,
            level=credit_level(score_after),
        )
