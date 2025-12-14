from decimal import Decimal
import math

CATEGORY_K = {
    "mobile": 0.35,
    "tablet": 0.28,
    "computer": 0.20,
    "laptop": 0.22,
    "console": 0.18,
    "camera": 0.15,
    "wearable": 0.30,
    "audio": 0.30,
    "drone": 0.22,
}

CATEGORY_VOL = {
    "mobile": 0.12,
    "tablet": 0.10,
    "computer": 0.10,
    "laptop": 0.10,
    "console": 0.09,
    "camera": 0.08,
    "wearable": 0.12,
    "audio": 0.12,
    "drone": 0.11,
}

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def exp_decay(k: float, years: float) -> Decimal:
    return Decimal(str(math.exp(-k * years)))

def estimate_range(original_price: Decimal, years_used: float, grade_factor: Decimal, defect_penalty: Decimal, category_code: str):
    k = CATEGORY_K.get(category_code, 0.20)
    base_vol = CATEGORY_VOL.get(category_code, 0.10)

    age_factor = exp_decay(k, years_used)
    defect_penalty = clamp(defect_penalty, Decimal("0"), Decimal("0.65"))
    defect_factor = Decimal("1") - defect_penalty

    mid = original_price * grade_factor * age_factor * defect_factor

    volatility = Decimal(str(base_vol)) + (Decimal("0.08") * defect_penalty)
    volatility = clamp(volatility, Decimal("0.06"), Decimal("0.25"))

    min_p = mid * (Decimal("1") - volatility)
    max_p = mid * (Decimal("1") + volatility)

    min_p = max(min_p, Decimal("50"))
    max_p = max(max_p, min_p)

    return {
        "estimated_mid": mid.quantize(Decimal("0.01")),
        "estimated_min": min_p.quantize(Decimal("0.01")),
        "estimated_max": max_p.quantize(Decimal("0.01")),
        "volatility": float(volatility),
        "age_factor": float(age_factor),
        "defect_penalty": float(defect_penalty),
    }

def compare_price(selling_price: Decimal, estimated_min: Decimal, estimated_max: Decimal):
    # 高于 max 或低于 min 才给百分比；区间内为 0
    if selling_price > estimated_max:
        diff = (selling_price - estimated_max) / estimated_max * Decimal("100")
        return float(diff), f"高于市场价 {float(diff):.1f}%"
    if selling_price < estimated_min:
        diff = (estimated_min - selling_price) / estimated_min * Decimal("100")
        return -float(diff), f"低于市场价 {float(diff):.1f}%"
    return 0.0, "合理区间内"

def value_score_from_diff(diff_pct: float) -> float:
    # diff_pct: 高于为正，低于为负
    score = 100.0 - max(0.0, diff_pct)
    return max(0.0, min(100.0, score))