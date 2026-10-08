"""
PCMarket.vn Web Crawler for PC Parts
Extracts structured product data including pricing, specs, images, warranty, and stock status.
Supports multi-threaded scraping and incremental progress saving.
"""

import sys
import re
import os
import time
import json
import argparse
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Ensure UTF-8 output on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

KNOWN_CATEGORIES = {
    "vga": "https://pcmarket.vn/vga-card-man-hinh.html",
    "cpu": "https://pcmarket.vn/cpu-bo-vi-xu-ly.html",
    "mainboard": "https://pcmarket.vn/mainboard-bo-mach-chu.html",
    "ram": "https://pcmarket.vn/ram-bo-nho-trong.html",
    "ssd": "https://pcmarket.vn/o-cung-ssd.html",
    "hdd": "https://pcmarket.vn/o-cung-hdd.html",
    "psu": "https://pcmarket.vn/psu-nguon-may-tinh.html",
    "case": "https://pcmarket.vn/case-vo-may-tinh.html",
    "cooling": "https://pcmarket.vn/tan-nhiet-cooling.html",
    "monitor": "https://pcmarket.vn/monitor-man-hinh.html",
}

class PCMarketCrawler:
    def __init__(self, delay: float = 0.1, concurrency: int = 8):
        self.delay = delay
        self.concurrency = concurrency
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _get(self, url: str) -> BeautifulSoup:
        if self.delay > 0:
            time.sleep(self.delay)
        response = self.session.get(url, timeout=25)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')

    @staticmethod
    def clean_number(text: str):
        if not text:
            return None
        digits = re.sub(r'[^\d]', '', str(text))
        return int(digits) if digits else None

    def parse_product(self, product_url: str) -> dict:
        """Parse full product details from a product page."""
        try:
            # Create a separate session per worker thread to avoid contention
            s = requests.Session()
            s.headers.update(DEFAULT_HEADERS)
            resp = s.get(product_url, timeout=25)
            if resp.status_code != 200:
                print(f"[!] HTTP {resp.status_code} for {product_url}")
                return None
            soup = BeautifulSoup(resp.text, 'lxml')
        except Exception as e:
            print(f"[!] Error fetching {product_url}: {e}")
            return None

        # Remove script and style elements to avoid grabbing JS templates in searches
        for unwanted in soup(['script', 'style', 'noscript', 'iframe']):
            unwanted.decompose()

        # Title
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else ""

        # Price elements
        market_price_el = soup.select_one('#js-market-price, del')
        market_price = self.clean_number(market_price_el.get_text()) if market_price_el else None

        sale_price_el = soup.select_one('.pro-price, .js-variant-price')
        sale_price = self.clean_number(sale_price_el.get_text()) if sale_price_el else None

        discount_el = soup.select_one('.pro-sale_off, .p-discount')
        discount_rate = discount_el.get_text(strip=True) if discount_el else None
        if not discount_rate and sale_price and market_price and market_price > sale_price:
            discount_pct = round((1 - sale_price / market_price) * 100)
            discount_rate = f"-{discount_pct}%"

        # Warranty
        warranty = None
        warranty_match = soup.find(string=re.compile(r'Bảo hành:\s*', re.IGNORECASE))
        if warranty_match:
            clean_w = warranty_match.strip()
            if 0 < len(clean_w) <= 50 and '\n' not in clean_w:
                warranty = clean_w

        # Breadcrumbs
        breadcrumbs = [
            a.get_text(strip=True)
            for a in soup.select('.breadcrumb a, [class*="breadcrumb"] a')
            if a.get_text(strip=True)
        ]

        # Technical Specifications
        specs = {}
        spec_table = soup.find('table', class_=lambda c: not c or 'pro-info-price' not in c)
        if spec_table:
            for tr in spec_table.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 2:
                    key = tds[0].get_text(strip=True)
                    val = tds[1].get_text(strip=True)
                    if key and val:
                        specs[key] = val

        # Brand extraction (check multiple keys or title heuristics)
        brand = (
            specs.get("Nhà sản xuất")
            or specs.get("Hãng sản xuất")
            or specs.get("Hãng")
            or specs.get("Thương hiệu", "")
        )
        if not brand and title:
            known_brands = [
                "ASUS", "ROG", "GIGABYTE", "AORUS", "MSI", "COLORFUL", "IGAME",
                "ZOTAC", "GALAX", "INNO3D", "PALIT", "SAPPHIRE", "LEADTEK",
                "JGINYUE", "INTEL", "AMD", "CORSAIR", "KINGSTON", "GSKILL",
                "SAMSUNG", "WESTERN DIGITAL", "SEAGATE", "COOLER MASTER", "NZXT",
                "AFOX", "BIOSTAR", "PNY", "OCPC", "YESTON"
            ]
            for kb in known_brands:
                if re.search(rf'\b{re.escape(kb)}\b', title, re.IGNORECASE):
                    brand = kb.capitalize()
                    break

        # Model extraction
        model = (
            specs.get("Model")
            or specs.get("Mã sản phẩm")
            or specs.get("Mã SP", "")
        )

        # High resolution gallery images
        images = []
        for img in soup.select('.product-image img, .gallery img, #sync1 img, #sync2 img, .slider-for img, .owl-carousel img'):
            src = img.get('src') or img.get('data-src')
            if src and ('product' in src or 'media' in src):
                clean_src = re.sub(r'/(250_|thumb_)', '/', src)
                full_img_url = urljoin("https://pcmarket.vn", clean_src)
                if full_img_url not in images:
                    images.append(full_img_url)

        # Stock / availability status
        stock = "In Stock"
        if soup.find(string=re.compile(r'Hết hàng|Liên hệ', re.IGNORECASE)):
            stock = "Contact / Out of stock"

        return {
            "title": title,
            "url": product_url,
            "brand": brand,
            "model": model,
            "sale_price": sale_price,
            "market_price": market_price,
            "discount_rate": discount_rate,
            "warranty": warranty,
            "stock": stock,
            "breadcrumbs": breadcrumbs,
            "specs": specs,
            "images": images,
        }

    def get_category_product_urls(self, category_url: str, max_pages: int = 999) -> list:
        """Extract all product page URLs across pages of a category."""
        product_urls = []
        current_page = 1

        print(f"[*] Discovering product URLs in category: {category_url}")
        while current_page <= max_pages:
            if current_page == 1:
                page_url = category_url
            else:
                sep = "&" if "?" in category_url else "?"
                page_url = f"{category_url}{sep}page={current_page}"

            try:
                soup = self._get(page_url)
            except Exception as e:
                print(f"[!] Failed to fetch page {page_url}: {e}")
                break

            items = soup.select('.p-item')
            if not items:
                print(f"[*] Page {current_page} returned 0 products. Reached end of category.")
                break

            found_this_page = 0
            for item in items:
                link_el = item.select_one('a.p-img, a.p-name')
                if link_el and link_el.get('href'):
                    full_link = urljoin("https://pcmarket.vn", link_el['href'])
                    if full_link not in product_urls:
                        product_urls.append(full_link)
                        found_this_page += 1

            print(f"    Page {current_page}: found {found_this_page} items (Total: {len(product_urls)})")

            # Check if current_page matches max page in pagination
            pages = [int(a.get_text(strip=True)) for a in soup.select('.paging a, .pagination a') if a.get_text(strip=True).isdigit()]
            if pages and current_page >= max(pages):
                print(f"[*] Reached last page ({current_page}) in pagination.")
                break

            current_page += 1

        return product_urls

    def crawl_category(self, category_url: str, max_pages: int = 999, max_items: int = None, output_base: str = None) -> list:
        """Crawl products with multi-threading and periodic saving."""
        urls = self.get_category_product_urls(category_url, max_pages=max_pages)
        if max_items:
            urls = urls[:max_items]

        total = len(urls)
        print(f"\n[*] Starting multi-threaded scraping for {total} products (threads={self.concurrency})...")
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_to_url = {executor.submit(self.parse_product, url): url for url in urls}
            for future in as_completed(future_to_url):
                completed += 1
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                except Exception as e:
                    print(f"[!] Error on {future_to_url[future]}: {e}")

                if completed % 25 == 0 or completed == total:
                    pct = (completed / total) * 100
                    print(f"[*] Progress: {completed}/{total} ({pct:.1f}%) scraped...")
                    if output_base:
                        # Periodic intermediate save
                        self.save_json(results, f"{output_base}.json")

        return results

    @staticmethod
    def save_json(data: list, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def export(cls, data: list, output_base: str):
        """Export crawled data to JSON format."""
        if not data:
            print("[!] No data to export.")
            return

        json_path = f"{output_base}.json"
        cls.save_json(data, json_path)
        print(f"[✓] Saved JSON ({len(data)} items) to {json_path}")


def main():
    parser = argparse.ArgumentParser(description="PCMarket.vn Web Crawler")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Crawl a single product URL")
    group.add_argument("--category", help="Category URL or shortcode (e.g. 'vga', 'cpu', 'ram')")

    parser.add_argument("--pages", type=int, default=999, help="Max category pages to crawl (default: all)")
    parser.add_argument("--max-items", type=int, default=None, help="Limit number of items to crawl")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between requests in seconds")
    parser.add_argument("--threads", type=int, default=8, help="Number of concurrent threads (default: 8)")
    parser.add_argument("--out", default="vga_pcmarket", help="Output file base name (without extension)")

    args = parser.parse_args()
    crawler = PCMarketCrawler(delay=args.delay, concurrency=args.threads)

    if args.url:
        print(f"[*] Crawling single product: {args.url}")
        res = crawler.parse_product(args.url)
        if res:
            crawler.export([res], args.out)
    else:
        cat_url = KNOWN_CATEGORIES.get(args.category.lower(), args.category)
        print(f"[*] Crawling category: {cat_url}")
        results = crawler.crawl_category(cat_url, max_pages=args.pages, max_items=args.max_items, output_base=args.out)
        crawler.export(results, args.out)
        print(f"\n[✓] Finished crawling {len(results)} items!")

if __name__ == "__main__":
    main()
