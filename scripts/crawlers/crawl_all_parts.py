"""
Crawl all remaining PC component categories from PCMarket.vn
"""

import sys
import time
import json
import os
from crawler import PCMarketCrawler, KNOWN_CATEGORIES

sys.stdout.reconfigure(encoding='utf-8')

# Categories to crawl (excluding vga and cpu which are already done)
CATEGORIES_TO_CRAWL = {
    "mainboard": "https://pcmarket.vn/mainboard-bo-mach-chu.html",
    "ram": "https://pcmarket.vn/ram-bo-nho-trong.html",
    "ssd": "https://pcmarket.vn/o-cung-ssd.html",
    "hdd": "https://pcmarket.vn/o-cung-hdd.html",
    "psu": "https://pcmarket.vn/psu-nguon-may-tinh.html",
    "case": "https://pcmarket.vn/case-vo-may-tinh.html",
    "cooling": "https://pcmarket.vn/tan-nhiet-cooling.html",
    "monitor": "https://pcmarket.vn/monitor-man-hinh.html",
}

def main():
    crawler = PCMarketCrawler(delay=0.05, concurrency=10)
    summary = {}

    start_total = time.time()
    for cat_name, cat_url in CATEGORIES_TO_CRAWL.items():
        print(f"\n{'='*60}")
        print(f"[*] CRAWLING CATEGORY: {cat_name.upper()} ({cat_url})")
        print(f"{'='*60}")

        start_cat = time.time()
        out_base = f"{cat_name}_pcmarket"
        results = crawler.crawl_category(cat_url, max_pages=999, output_base=out_base)
        crawler.export(results, out_base)

        elapsed = round(time.time() - start_cat, 1)
        summary[cat_name] = {
            "count": len(results),
            "file": f"{out_base}.json",
            "time_seconds": elapsed
        }
        print(f"[✓] {cat_name.upper()} finished: {len(results)} items in {elapsed}s")

    print("\n" + "="*60)
    print("ALL REMAINING CATEGORIES COMPLETED!")
    print(f"Total time elapsed: {round(time.time() - start_total, 1)}s")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
