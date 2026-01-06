import csv
import re
import time
from urllib.parse import urljoin
import os

import requests
from lxml import etree

# Apple phones category - page 1


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

BASE = "https://detail.zol.com.cn"
SESSION = requests.Session()


def build_page_url(list_url: str, page: int) -> str:
    """Build a list page URL for the given page.

    Supports both:
    - Short form:  ..._list_1.html
    - Long form:   ..._list_1_0_1_2_0_1.html
    """
    # Short form: ..._list_{n}.html -> ..._list_{page}_0_1_2_0_{page}.html
    m_short = re.search(r"^(.*_list_)(\d+)\.html$", list_url)
    if m_short:
        prefix = m_short.group(1)
        return f"{prefix}{page}_0_1_2_0_{page}.html"

    # Long form (existing): replace trailing _{n}.html
    return re.sub(r"_(\d+)\.html$", f"_{page}.html", list_url)


def fetch_html(url: str, referer: str | None = None) -> etree._Element | None:
    # Add a few headers that help with sites expecting browser-like requests
    headers = dict(HEADERS)
    headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
    if referer:
        headers["Referer"] = referer

    last_status = None
    for attempt in range(1, 7):
        try:
            resp = SESSION.get(url, headers=headers, timeout=15)
            last_status = resp.status_code
        except Exception as e:
            print(f"[FETCH_ERR] attempt={attempt} url={url} err={e}")
            time.sleep(0.6 * attempt)
            continue

        if resp.status_code == 200:
            return etree.HTML(resp.content)

        # Debug non-200 (403/404/etc)
        snippet = resp.text[:160].replace("\n", " ") if resp.text else ""
        print(f"[FETCH_FAIL] attempt={attempt} status={resp.status_code} url={url} snippet={snippet}")

        # 503 is often temporary (openService Temporarily Unavailable). Backoff longer.
        if resp.status_code == 503:
            time.sleep(2.0 * attempt)
        else:
            time.sleep(0.9 * attempt)

    print(f"[FETCH_GIVEUP] status={last_status} url={url}")
    return None


def get_next_page_url(doc: etree._Element, current_url: str) -> str | None:
    """Return absolute next-page URL based on pagebar's <a class='next'>.

    XPath requirements:
    - first locate div.page-box
    - then div.pagebar
    - then a.next
    """
    next_hrefs = doc.xpath('//div[@class="page-box"]/div[@class="pagebar"]/a[@class="next"]/@href')
    print("下一页的url是，", next_hrefs)
    if not next_hrefs:
        return None
    return urljoin(current_url, next_hrefs[0])


def discover_brands(start_doc: etree._Element, current_url: str, limit: int = 10) -> list[dict]:
    """Discover top brand links from div#J_ParamBrand.

    Expected HTML:
    <div id="J_ParamBrand" ...>
        <span ...>不限</span>
        <a href="...">华为</a><a href="...">vivo</a>...
    </div>

    Returns list of dicts: {brand, url, index_type}
    where index_type is like 'cell_phone_index' extracted from the href.
    """
    # Use direct-child <a> to preserve ordering and avoid unrelated nested anchors
    anchors = start_doc.xpath('//div[@id="J_ParamBrand"]/a')
    anchors = anchors[1:11]

    # DEBUG: inspect the brand container and extracted anchors
    brand_div = start_doc.xpath('//div[@id="J_ParamBrand"]')
    if brand_div:
        html = etree.tostring(brand_div[0], encoding="unicode", method="html")
        print("========== J_ParamBrand HTML ==========")
        print(html)
        print("======================================")

    print("========== anchors(debug) ==========")
    for i, a in enumerate(anchors[:50], start=1):
        txt = ("".join(a.xpath('.//text()'))).strip()
        href = (a.xpath('./@href') or [""])[0]
        cls = a.attrib.get('class', '')
        print(f"{i:02d}. text={txt!r} href={href!r} class={cls!r}")
    print("===================================")
    brands: list[dict] = []
    for a in anchors:
        name = ("".join(a.xpath('.//text()'))).strip()
        hrefs = a.xpath('./@href')
        if not name or not hrefs:
            continue

        url = urljoin(current_url, hrefs[0])

        # e.g. https://detail.zol.com.cn/cell_phone_index/subcate57_613_list_1.html -> cell_phone_index
        m = re.search(r"https?://[^/]+/([^/]+)/", url)
        index_type = m.group(1) if m else ""

        brands.append({"brand": name, "url": url, "index_type": index_type})
        if len(brands) >= limit:
            break

    # Debug (keep short): show the extracted brands
    if not brands:
        print("[BRAND_DEBUG] no brands found in #J_ParamBrand")
    else:
        print("[BRAND_DEBUG] top brands:", [b["brand"] for b in brands])

    return brands


def parse_list_page(doc: etree._Element, brand: str, index_type: str) -> list[dict]:
    """Parse one list page and return product dicts."""
    items = doc.xpath('//ul[@id="J_PicMode"]/li')
    results: list[dict] = []

    for li in items:
        a_list = li.xpath('.//a[@class="pic"]')
        if not a_list:
            continue
        a = a_list[0]

        href_list = a.xpath('./@href')
        if not href_list:
            continue
        detail_url = urljoin(BASE, href_list[0])

        img_list = a.xpath('.//img')
        if not img_list:
            continue
        img = img_list[0]

        # ZOL uses odd lazy-load attribute names (e.g. .src)
        image_url = (
            img.attrib.get('.src')
            or img.attrib.get('data-src')
            or img.attrib.get('data-original')
            or img.attrib.get('src')
        )

        name_list = img.xpath('./@alt')
        name = name_list[0].strip() if name_list else ""

        # Reference price on list page: “参考价：” -> span.price -> two <b> values
        price_sign = li.xpath(
            './/div[contains(@class,"price-row")]'
            '//span[contains(@class,"price-tip") and contains(normalize-space(.),"参考价")]/'
            'following-sibling::span[contains(@class,"price")][1]/'
            'b[contains(@class,"price-sign")]/text()'
        )
        price_num = li.xpath(
            './/div[contains(@class,"price-row")]'
            '//span[contains(@class,"price-tip") and contains(normalize-space(.),"参考价")]/'
            'following-sibling::span[contains(@class,"price")][1]/'
            'b[contains(@class,"price-type")]/text()'
        )
        price = ((price_sign[0].strip() if price_sign else "") + (price_num[0].strip() if price_num else "")).strip()

        # Example detail url: /cell_phone/index2139583.shtml
        m = re.search(r"index(\d+)\.shtml", detail_url)
        sku_id = m.group(1) if m else None

        if not sku_id:
            continue

        results.append({
            "index_type": index_type,
            "brand": brand,
            "sku_id": sku_id,
            "name": name,
            "price": price,
            "image_url": image_url or "",
            "detail_url": detail_url,
            "source": "ZOL",
        })

    return results


def crawl_all_pages(list_url: str, brand: str, index_type: str, max_pages: int = 200, sleep_sec: float = 0.6) -> list[dict]:
    """Crawl list pages by following the explicit <a class='next'> link.

    Stops when:
    - no next page link exists, or
    - a page returns no rows, or
    - max_pages reached.

    Also de-duplicates by sku_id.
    """
    seen_sku: set[str] = set()
    all_rows: list[dict] = []

    url = list_url
    prev_url: str | None = None
    for page_idx in range(1, max_pages + 1):
        print(f"[FETCH] page={page_idx} url={url}")
        doc = fetch_html(url, referer=prev_url or BASE)
        if doc is None:
            # One more longer wait and retry the same URL once (helps with transient 503)
            print(f"[RETRY_ONCE] url={url}")
            time.sleep(6)
            doc = fetch_html(url, referer=prev_url or BASE)
            if doc is None:
                break

        rows = parse_list_page(doc, brand=brand, index_type=index_type)
        if not rows:
            break

        for r in rows:
            sku = r["sku_id"]
            if sku in seen_sku:
                continue
            seen_sku.add(sku)
            all_rows.append(r)

        print(f"[OK] page={page_idx} items={len(rows)} total_unique={len(all_rows)}")

        next_url = get_next_page_url(doc, url)
        print(f"[NEXT] {next_url}")
        if not next_url:
            break

        # Use current page as referer for the next page
        prev_url = url
        url = next_url
        time.sleep(sleep_sec)

    return all_rows


def export_csv(rows: list[dict], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    fieldnames = ["index_type", "brand", "sku_id", "name", "price", "image_url", "detail_url", "source"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


if __name__ == "__main__":
    # Start from any brand-list page under a given index type
    START_URL = "https://detail.zol.com.cn/cell_phone_index/subcate57_list_1.html"

    start_doc = fetch_html(START_URL, referer=BASE)
    if start_doc is None:
        print("[RETRY_START] retrying start page after 6s")
        time.sleep(6)
        start_doc = fetch_html(START_URL, referer=BASE)
    if start_doc is None:
        raise SystemExit("Failed to fetch start page")

    brands = discover_brands(start_doc, START_URL, limit=10)
    if not brands:
        raise SystemExit("No brands discovered from J_ParamBrand")

    all_rows: list[dict] = []
    for b in brands:
        print(f"\n=== BRAND: {b['brand']} ({b['url']}) ===")
        rows = crawl_all_pages(b["url"], brand=b["brand"], index_type=b["index_type"], max_pages=200, sleep_sec=0.9)
        all_rows.extend(rows)

    # Output file name follows the index type in START_URL, e.g. notebook_index -> zol_products/notebook_index.csv
    m = re.search(r"https?://[^/]+/([^/]+)/", START_URL)
    start_index_type = m.group(1) if m else "products"
    out = f"zol_products/{start_index_type}.csv"
    export_csv(all_rows, out)
    print(f"\nSaved: {out} (rows={len(all_rows)})")