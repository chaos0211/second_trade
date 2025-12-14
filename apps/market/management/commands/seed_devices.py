from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.market.models import Category, Brand, DeviceModel, MarketPriceStat


def D(x: int | float | str) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"))


class Command(BaseCommand):
    help = "Seed 8 categories x 30 device models with MarketPriceStat (>=240 rows)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing DeviceModel/Brand/Category/MarketPriceStat before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        if options.get("reset"):
            # 注意：如果你已有业务数据（商品/订单）请不要 reset
            MarketPriceStat.objects.all().delete()
            DeviceModel.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()

        # 至少 8 类别
        categories = [
            "手机",
            "平板",
            "笔记本",
            "游戏机",
            "相机",
            "智能手表",
            "耳机音频",
            "显示器外设",
        ]

        cat_map = {}
        for name in categories:
            cat, _ = Category.objects.get_or_create(name=name)
            cat_map[name] = cat

        def get_brand(cat_name: str, brand_name: str) -> Brand:
            return Brand.objects.get_or_create(name=brand_name, category=cat_map[cat_name])[0]

        def make_market_stat(device: DeviceModel, base_price: Decimal):
            """
            生成市场价区间（p10/p50/p90），用于比价和性价比排序。
            规则：p50 围绕 base 轻微波动；p10/p90 分别偏离 8%~18%
            """
            base = D(base_price)
            # 中位价轻微抖动 +-3%
            mid = (base * D(1 + random.uniform(-0.03, 0.03))).quantize(D("0.01"))

            low_k = D(1 - random.uniform(0.08, 0.18))
            high_k = D(1 + random.uniform(0.08, 0.18))

            p10 = (mid * low_k).quantize(D("0.01"))
            p90 = (mid * high_k).quantize(D("0.01"))

            MarketPriceStat.objects.update_or_create(
                device_model=device,
                defaults={
                    "p10_price": p10,
                    "p50_price": mid,
                    "p90_price": p90,
                    "sample_size": random.randint(30, 300),
                },
            )

        created_count = 0

        # =========================
        # 1) 手机：iPhone 12-17（17沿用16价格）
        # 要求：每类至少30条，这里用多个档位+容量凑到>=30
        # =========================
        apple_phone = get_brand("手机", "Apple")

        # 基础价字典（你要求：iPhone17 用 iPhone16 的价格）
        # 这里定义 iPhone16 的“参考价”，iPhone17 直接复用
        iphone_base = {
            12: {128: 3999, 256: 4599, 512: 5599},
            13: {128: 4299, 256: 4999, 512: 6099},
            14: {128: 4699, 256: 5499, 512: 6699},
            15: {128: 5299, 256: 6099, 512: 7499},
            16: {128: 5999, 256: 6999, 512: 8999},
            17: {128: 5999, 256: 6999, 512: 8999},  # 17沿用16
        }

        # Pro/Pro Max 用系数加成（保持真实感）
        tier_mult = {
            "": 1.00,
            "Pro": 1.20,
            "Pro Max": 1.35,
        }

        # 生成：6代 * 3容量 * 3档位 = 54 条（>30）
        for gen in range(12, 18):
            for storage in (128, 256, 512):
                for tier, mult in tier_mult.items():
                    name = f"iPhone {gen} {tier}".strip()
                    base_price = D(iphone_base[gen][storage] * mult)
                    model = DeviceModel.objects.get_or_create(
                        brand=apple_phone,
                        name=f"{name} {storage}GB",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 2) 平板：iPad
        # =========================
        apple_pad = get_brand("平板", "Apple")
        ipad_lines = [
            ("iPad", [64, 256], [2999, 3999]),
            ("iPad Air", [128, 256, 512], [4599, 5299, 6999]),
            ("iPad Pro 11", [128, 256, 512], [6799, 7499, 8999]),
            ("iPad Pro 13", [256, 512, 1024], [8999, 10499, 12999]),
        ]
        # 生成>=30：多代号/年份模拟
        years = ["2021", "2022", "2023", "2024", "2025"]
        for line, storages, bases in ipad_lines:
            for y in years:
                for s, b in zip(storages, bases):
                    base_price = D(b * (1 + random.uniform(-0.06, 0.06)))
                    model = DeviceModel.objects.get_or_create(
                        brand=apple_pad,
                        name=f"{y} {line} {s}GB",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 3) 笔记本：MacBook / Windows
        # =========================
        apple_nb = get_brand("笔记本", "Apple")
        lenovo_nb = get_brand("笔记本", "Lenovo")
        asus_nb = get_brand("笔记本", "ASUS")

        # MacBook：用“Air/Pro 13/Pro 14/Pro 16”组合凑>=30
        mac_lines = [
            ("MacBook Air 13", [8, 16], [256, 512], [7999, 9999]),
            ("MacBook Pro 13", [8, 16], [256, 512], [9999, 11999]),
            ("MacBook Pro 14", [16, 32], [512, 1024], [12999, 16999]),
            ("MacBook Pro 16", [16, 32], [512, 1024], [15999, 19999]),
        ]
        chips = ["M2", "M3", "M4"]  # 真实历史范围内
        for chip in chips:
            for line, rams, ssds, base_list in mac_lines:
                for ram in rams:
                    for ssd in ssds:
                        base = random.choice(base_list)
                        base_price = D(base * (1 + random.uniform(-0.05, 0.05)))
                        model = DeviceModel.objects.get_or_create(
                            brand=apple_nb,
                            name=f"{line} {chip} {ram}G {ssd}G",
                            defaults={"base_price": base_price},
                        )[0]
                        make_market_stat(model, base_price)
                        created_count += 1

        # Windows 本：ThinkPad/小新/ROG
        win_templates = [
            (lenovo_nb, "ThinkPad X1 Carbon", [16, 32], [512, 1024], [9999, 12999, 15999]),
            (lenovo_nb, "小新 Pro", [16, 32], [512, 1024], [5999, 6999, 8999]),
            (asus_nb, "ROG 幻", [16, 32], [512, 1024], [7999, 9999, 12999]),
        ]
        for brand, name, rams, ssds, bases in win_templates:
            for ram in rams:
                for ssd in ssds:
                    base = random.choice(bases)
                    base_price = D(base * (1 + random.uniform(-0.08, 0.08)))
                    model = DeviceModel.objects.get_or_create(
                        brand=brand,
                        name=f"{name} {ram}G {ssd}G",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 4) 游戏机
        # =========================
        nintendo = get_brand("游戏机", "Nintendo")
        sony = get_brand("游戏机", "Sony")
        xbox = get_brand("游戏机", "Microsoft")

        consoles = [
            (nintendo, "Switch", [2299, 2499, 2699]),
            (nintendo, "Switch OLED", [2799, 2999, 3199]),
            (sony, "PS4", [1599, 1799, 1999]),
            (sony, "PS5", [3299, 3699, 3999]),
            (xbox, "Xbox Series S", [1799, 1999, 2199]),
            (xbox, "Xbox Series X", [2999, 3299, 3599]),
        ]
        # 组合版本/套装凑>=30
        variants = ["标准版", "国行", "套装A", "套装B", "限定版"]
        for brand, name, base_list in consoles:
            for v in variants:
                base = random.choice(base_list)
                base_price = D(base * (1 + random.uniform(-0.10, 0.10)))
                model = DeviceModel.objects.get_or_create(
                    brand=brand,
                    name=f"{name} {v}",
                    defaults={"base_price": base_price},
                )[0]
                make_market_stat(model, base_price)
                created_count += 1

        # =========================
        # 5) 相机
        # =========================
        canon = get_brand("相机", "Canon")
        sony_cam = get_brand("相机", "Sony")
        fuji = get_brand("相机", "Fujifilm")

        cams = [
            (canon, "EOS R", [6999, 8999, 10999]),
            (canon, "EOS M", [2999, 3999, 4999]),
            (sony_cam, "Alpha A7", [9999, 12999, 15999]),
            (sony_cam, "ZV", [3999, 4999, 5999]),
            (fuji, "X-T", [6999, 8999, 10999]),
            (fuji, "X-S", [4999, 5999, 6999]),
        ]
        gens = ["II", "III", "IV", "V"]
        for brand, line, base_list in cams:
            for g in gens:
                for kit in ["机身", "18-55套机", "定焦套装"]:
                    base = random.choice(base_list)
                    kit_mult = {"机身": 1.0, "18-55套机": 1.15, "定焦套装": 1.20}[kit]
                    base_price = D(base * kit_mult * (1 + random.uniform(-0.10, 0.10)))
                    model = DeviceModel.objects.get_or_create(
                        brand=brand,
                        name=f"{line} {g} {kit}",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 6) 智能手表
        # =========================
        apple_watch = get_brand("智能手表", "Apple")
        huawei_watch = get_brand("智能手表", "Huawei")
        garmin = get_brand("智能手表", "Garmin")

        watches = [
            (apple_watch, "Apple Watch Series", [2499, 2999, 3499]),
            (apple_watch, "Apple Watch Ultra", [5999, 6999, 7999]),
            (huawei_watch, "Watch GT", [999, 1299, 1599]),
            (huawei_watch, "Watch", [1299, 1699, 1999]),
            (garmin, "Fenix", [3499, 4999, 6499]),
            (garmin, "Forerunner", [1999, 2499, 2999]),
        ]
        for brand, line, base_list in watches:
            for gen in range(4, 10):  # 模拟代际
                for size in ["41mm", "45mm", "49mm"]:
                    base = random.choice(base_list)
                    base_price = D(base * (1 + random.uniform(-0.12, 0.12)))
                    model = DeviceModel.objects.get_or_create(
                        brand=brand,
                        name=f"{line} {gen} {size}",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 7) 耳机音频
        # =========================
        apple_audio = get_brand("耳机音频", "Apple")
        sony_audio = get_brand("耳机音频", "Sony")
        bose = get_brand("耳机音频", "Bose")
        senn = get_brand("耳机音频", "Sennheiser")

        audios = [
            (apple_audio, "AirPods", [999, 1299, 1499]),
            (apple_audio, "AirPods Pro", [1699, 1999, 2299]),
            (apple_audio, "AirPods Max", [3999, 4499, 4999]),
            (sony_audio, "WH-1000X", [1999, 2499, 2999]),
            (bose, "QC", [1799, 2199, 2599]),
            (senn, "Momentum", [1999, 2499, 2999]),
        ]
        versions = ["一代", "二代", "三代", "四代", "五代"]
        for brand, line, base_list in audios:
            for v in versions:
                for pack in ["标准", "套装", "联名"]:
                    mult = {"标准": 1.0, "套装": 1.05, "联名": 1.10}[pack]
                    base = random.choice(base_list)
                    base_price = D(base * mult * (1 + random.uniform(-0.15, 0.15)))
                    model = DeviceModel.objects.get_or_create(
                        brand=brand,
                        name=f"{line} {v} {pack}",
                        defaults={"base_price": base_price},
                    )[0]
                    make_market_stat(model, base_price)
                    created_count += 1

        # =========================
        # 8) 显示器外设（显示器/键鼠/显卡坞）
        # =========================
        dell = get_brand("显示器外设", "Dell")
        lg = get_brand("显示器外设", "LG")
        logi = get_brand("显示器外设", "Logitech")
        razer = get_brand("显示器外设", "Razer")

        peripherals = [
            (dell, "UltraSharp", [1999, 2499, 2999, 3499]),
            (lg, "UltraGear", [1799, 2299, 2799, 3299]),
            (logi, "MX Master", [499, 699, 899]),
            (logi, "MX Keys", [599, 799, 999]),
            (razer, "机械键盘", [699, 899, 1199]),
            (razer, "扩展坞", [599, 799, 999]),
        ]
        for brand, line, base_list in peripherals:
            for spec in ["入门", "标准", "高配", "旗舰", "电竞", "办公"]:
                base = random.choice(base_list)
                base_price = D(base * (1 + random.uniform(-0.12, 0.12)))
                model = DeviceModel.objects.get_or_create(
                    brand=brand,
                    name=f"{line} {spec}",
                    defaults={"base_price": base_price},
                )[0]
                make_market_stat(model, base_price)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seed done. created/updated: {created_count} device models (>=240 expected)."))