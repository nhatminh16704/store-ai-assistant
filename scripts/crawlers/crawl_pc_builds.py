"""
Crawl Pre-built PC sets (Gaming, Workstation, Office, AI, Mini) from PCMarket.vn
"""

import sys
import time
import json
from crawler import PCMarketCrawler

sys.stdout.reconfigure(encoding='utf-8')

PC_CATEGORIES = {
    "pc_gaming": "https://pcmarket.vn/bo-pc-gaming-livestream.html",
    "pc_workstation": "https://pcmarket.vn/pc-workstation.html",
    "pc_office": "https://pcmarket.vn/pc-van-phong.html",
    "pc_ai": "https://pcmarket.vn/pc-ai",
    "pc_mini": "https://pcmarket.vn/pc-mini.html",
}

def main():
    crawler = PCMarketCrawler(delay=0.05, concurrency=10)
    all_pc_builds = []
    summary = {}
    start_total = time.time()

    for cat_name, cat_url in PC_CATEGORIES.items():
        print(f"\n{'='*60}")
        print(f"[*] CRAWLING PRE-BUILT PC: {cat_name.upper()} ({cat_url})")
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
        all_pc_builds.extend(results)
        print(f"[✓] {cat_name.upper()} finished: {len(results)} items in {elapsed}s")

    # Save consolidated file
    consolidated_file = "pc_builds_pcmarket.json"
    with open(consolidated_file, "w", encoding="utf-8") as f:
        json.dump(all_pc_builds, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print(f"ALL PRE-BUILT PC CATEGORIES COMPLETED! Total: {len(all_pc_builds)} PCs in {round(time.time() - start_total, 1)}s")
    print(f"Consolidated file saved: {consolidated_file}")
    for k, v in summary.items():
        print(f"  - {k.upper()}: {v['count']} items -> {v['file']}")

if __name__ == "__main__":
    main()
