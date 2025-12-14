import random
import time
from decimal import Decimal

class AIService:
    """
    模拟AI识别与估价服务
    """

    @staticmethod
    def analyze_image(image_path: str):
        time.sleep(0.3)

        mock_defects_pool = [
            "屏幕细微划痕", "边框磨损", "摄像头积灰", "背板凹陷", "无明显瑕疵"
        ]
        detected = random.sample(mock_defects_pool, k=random.randint(0, 2))

        if "无明显瑕疵" in detected:
            score = random.randint(95, 99)
            label = "99新"
            detected = []
        elif len(detected) == 0:
            score = random.randint(90, 95)
            label = "95新"
        elif len(detected) == 1:
            score = random.randint(80, 89)
            label = "9成新"
        else:
            score = random.randint(60, 79)
            label = "8成新"

        return {"score": score, "label": label, "defects": detected}

    @staticmethod
    def calculate_price(original_price, condition_score):
        original_price = Decimal(str(original_price))
        score = Decimal(str(condition_score))
        base_depreciation = Decimal("0.8")
        condition_factor = score / Decimal("100")
        estimated = original_price * base_depreciation * condition_factor
        return round(estimated, -1)