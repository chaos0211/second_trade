import csv
import re
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.market.models import Category, Brand, DeviceModel


INDEX_TYPE_MAP = {
    "cell_phone_index": "手机",
    "notebook_index": "笔记本",
    "gpswatch": "智能手表",
    "zsyxj": "掌上游戏机",
    "digital_camera_index": "数码相机",
    "digital_tv": "数字电视",
    "game": "游戏机",
    "gpswatch": "智能手表",
    "keyboard": "键盘",
    "lcd": "显示器",
    "mice": "鼠标",
    "microphone": "麦克风",
    "mp3_player": "MP3",
    "speaker": "音箱",
    "vga": "显卡",
    "zsyxi": "掌上游戏机",
}


class Command(BaseCommand):
    help = "Import ZOL products CSV into DeviceModel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=False,
            help="CSV file path, e.g. zol_products/cell_phone_index.csv",
        )
        parser.add_argument(
            "--dir",
            type=str,
            required=False,
            default="zol_products",
            help="Directory containing CSV files, default: zol_products",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_opt = options.get("file")
        dir_opt = options.get("dir")

        csv_files: list[Path] = []

        if file_opt:
            csv_path = Path(file_opt)
            if not csv_path.exists():
                self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
                return
            csv_files = [csv_path]
        else:
            dir_path = Path(dir_opt or "zol_products")
            if not dir_path.exists() or not dir_path.is_dir():
                self.stderr.write(self.style.ERROR(f"CSV directory not found: {dir_path}"))
                return

            csv_files = sorted([p for p in dir_path.glob("*.csv") if p.is_file()])
            if not csv_files:
                self.stderr.write(self.style.WARNING(f"No CSV files found in: {dir_path}"))
                return

        created = 0
        updated = 0
        files_imported = 0

        for csv_path in csv_files:
            self.stdout.write(self.style.NOTICE(f"[IMPORT] {csv_path}"))
            files_imported += 1

            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                # 兼容：BOM/多余空格/大小写导致的 KeyError
                fieldnames = reader.fieldnames or []
                normalized_map = { (fn or "").strip().lstrip("\ufeff").lower(): (fn or "") for fn in fieldnames }

                def getv(row_dict: dict, key: str, default: str = "") -> str:
                    """Get value by header name, tolerant to BOM/whitespace/case."""
                    raw_key = normalized_map.get(key.lower())
                    if raw_key is None:
                        return default
                    val = row_dict.get(raw_key, default)
                    if val is None:
                        return default
                    return str(val).strip()

                # 若 CSV 本身缺少 index_type，则用文件名推断（例如 cell_phone_index.csv -> cell_phone_index）
                inferred_index_type = csv_path.stem.strip()

                for row in reader:
                    index_type = getv(row, "index_type") or inferred_index_type
                    brand_name = getv(row, "brand")
                    sku_id = getv(row, "sku_id")
                    name = getv(row, "name")
                    image_url = getv(row, "image_url")
                    detail_url = getv(row, "detail_url")

                    # price 可能为空/可能带￥等符号
                    price_raw = getv(row, "price")

                    # 兼容示例："￥10199" / "10199" / "￥10,199" / "暂无报价" / "-" / ""
                    price_norm = (price_raw or "").strip()
                    if price_norm:
                        # 去掉常见货币符号与分隔符
                        price_norm = price_norm.replace("￥", "").replace(",", "").replace("元", "").strip()

                        # 提取第一个数字（含小数）
                        m = re.search(r"(\d+(?:\.\d+)?)", price_norm)
                        if m:
                            try:
                                msrp_price = Decimal(m.group(1))
                            except Exception:
                                msrp_price = None
                        else:
                            msrp_price = None
                    else:
                        msrp_price = None

                    if not sku_id or not name:
                        self.stderr.write(self.style.WARNING(
                            f"Skip row with empty sku_id/name: sku_id={sku_id!r}, name={name!r} (file={csv_path.name})"
                        ))
                        continue

                    if not brand_name:
                        brand_name = "未知品牌"

                    # ---------- Category ----------
                    category_name = INDEX_TYPE_MAP.get(index_type)
                    if not category_name:
                        self.stderr.write(
                            self.style.WARNING(f"Unknown index_type: {index_type}")
                        )
                        continue

                    category, _ = Category.objects.get_or_create(
                        code=index_type,
                        defaults={"name": category_name},
                    )

                    # ---------- Brand ----------
                    brand, _ = Brand.objects.get_or_create(
                        category=category,
                        name=brand_name,
                    )

                    # ---------- DeviceModel (核心) ----------
                    obj, is_created = DeviceModel.objects.update_or_create(
                        zol_sku_id=sku_id,
                        defaults={
                            "name": name,
                            "brand": brand,
                            "msrp_price": msrp_price,
                            "image_url": image_url,
                            "detail_url": detail_url,
                        },
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished. files={files_imported}, created={created}, updated={updated}"
            )
        )