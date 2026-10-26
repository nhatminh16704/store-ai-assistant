"""
Crawl Gaming Gear (Keyboard, Mouse, Headphone) from PCMarket.vn
"""

import sys
import time
from crawler import PCMarketCrawler

sys.stdout.reconfigure(encoding='utf-8')

GEAR_CATEGORIES = {
    "keyboard": "https://pcmarket.vn/ban-phim-choi-game.html",
    "mouse": "https://pcmarket.vn/chuot-choi-game.html",
    "headphone": "https://pcmarket.vn/tai-nghe-choi-game.html",
}

def main():
    crawler = PCMarketCrawler(delay=0.05, concurrency=8)
    summary = {}
    start_total = time.time()

    for cat_name, cat_url in GEAR_CATEGORIES.items():
        print(f"\n{'='*60}")
        print(f"[*] CRAWLING GAMING GEAR: {cat_name.upper()} ({cat_url})")
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
    print("ALL GEAR CATEGORIES COMPLETED!")
    print(f"Total time elapsed: {round(time.time() - start_total, 1)}s")
    for k, v in summary.items():
        print(f"  - {k.upper()}: {v['count']} items -> {v['file']}")

if __name__ == "__main__":
    main()
