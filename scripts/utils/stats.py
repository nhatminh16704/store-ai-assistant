import json, glob, os, sys

sys.stdout.reconfigure(encoding='utf-8')

# Look in data/raw recursively or current dir
base_dir = os.path.join(os.path.dirname(__file__), "../../data/raw")
files = sorted(glob.glob(os.path.join(base_dir, "**/*_pcmarket.json"), recursive=True))
if not files:
    files = sorted(glob.glob('*_pcmarket.json'))

print(f"Tổng hợp {len(files)} danh mục linh kiện PC:")
print("-" * 90)
print(f"{'Danh mục':<12} | {'Số SP':<6} | {'Dung lượng':<10} | {'Khoảng giá (VND)':<30} | {'Top hãng'}")
print("-" * 90)

total_all = 0
total_size = 0

for f in files:
    cat = os.path.basename(f).replace('_pcmarket.json', '')
    size_kb = round(os.path.getsize(f) / 1024, 1)

    total_size += size_kb
    with open(f, 'r', encoding='utf-8') as fp:
        items = json.load(fp)
    total_all += len(items)
    prices = [x['sale_price'] for x in items if x.get('sale_price')]
    brands = {}
    for x in items:
        b = x.get('brand') or 'Chưa rõ'
        brands[b] = brands.get(b, 0) + 1
    top_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:3]
    top_b_str = ', '.join([f'{k} ({v})' for k, v in top_brands])
    
    min_p = f"{min(prices):,} đ" if prices else "Liên hệ"
    max_p = f"{max(prices):,} đ" if prices else "Liên hệ"
    price_range = f"{min_p} - {max_p}"
    print(f"{cat.upper():<12} | {len(items):>6} | {size_kb:>7} KB | {price_range:<30} | {top_b_str}")

print("-" * 90)
print(f"TỔNG CỘNG:   | {total_all:>6} | {round(total_size / 1024, 2):>7} MB")
