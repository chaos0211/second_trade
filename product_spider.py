import requests
from lxml import etree

URL = "https://detail.zol.com.cn/1951/1950439/param.shtml"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

resp = requests.get(URL, headers=headers, timeout=10)
resp.encoding = "gbk"  # ⚠️ ZOL 使用 GBK 编码
html = etree.HTML(resp.text)

# ========================
# 1. 产品名称
# ========================
product_name = html.xpath('//h1[@class="product-model__name"]/text()')
product_name = product_name[0].strip() if product_name else None

# ========================
# 2. 参考报价
# ========================
price = html.xpath('//a[@id="param-list-b2c-jd"]/text()')
price = price[0].strip() if price else None

# ========================
# 3. 上市日期（参数表）
# ========================
release_date = html.xpath(
    '//span[@id="newPmVal_1"]/text()'
)
release_date = release_date[0].strip() if release_date else None

result = {
    "product_name": product_name,
    "price": price,
    "release_date": release_date,
    "source": "ZOL 中关村在线"
}

print(result)