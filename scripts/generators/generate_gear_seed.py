"""
Generate seed JSON for Keyboard, Mouse, and Headset matching catalog_seed.json
Categories:
- MOUSE: name='Chuột', seo_name='mouse', hardware_type='MOUSE'
- KEYBOARD: name='Bàn phím', seo_name='keyboard', hardware_type='KEYBOARD'
- HEADSET: name='Tai nghe', seo_name='headset', hardware_type='HEADSET'
"""

import sys
import os
import re
import json
import time
import uuid
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

SYSTEM_ADMIN_ID = "018f0000-0000-7000-8000-000000000001"

# Exact Category definitions matching user's CTE & catalog_seed.json
CATEGORY_CONFIG = {
    "keyboard": {
        "id": "5d8465a2-3a9c-5688-9bd3-7dc5b452584a",
        "name": "Bàn phím",
        "seo_name": "keyboard",
        "hardware_type": "KEYBOARD",
        "code": "KB",
        "file": "keyboard_pcmarket.json"
    },
    "mouse": {
        "id": "92f1931a-79ca-5aed-b9b3-d29760b22865",
        "name": "Chuột",
        "seo_name": "mouse",
        "hardware_type": "MOUSE",
        "code": "MOU",
        "file": "mouse_pcmarket.json"
    },
    "headphone": {
        "id": "db4fbbca-54c0-552b-8b65-7506eeb09656",
        "name": "Tai nghe",
        "seo_name": "headset",
        "hardware_type": "HEADSET",
        "code": "HP",
        "file": "headphone_pcmarket.json"
    }
}

def generate_uuidv7():
    ts_ms = int(time.time() * 1000)
    rand_bytes = bytearray(os.urandom(16))
    rand_bytes[0:6] = ts_ms.to_bytes(6, byteorder='big')
    rand_bytes[6] = (rand_bytes[6] & 0x0F) | 0x70
    rand_bytes[8] = (rand_bytes[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(rand_bytes)))

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:200]

def parse_warranty_months(warranty_str, specs) -> int:
    text = f"{warranty_str or ''} {specs.get('Bảo hành', '')} {specs.get('Thời gian bảo hành', '')}"
    match = re.search(r'(\d+)\s*(tháng|thang|m|months)', text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if 1 <= val <= 120:
            return val
    year_match = re.search(r'(\d+)\s*(năm|nam|years|yr)', text, re.IGNORECASE)
    if year_match:
        val = int(year_match.group(1)) * 12
        if 1 <= val <= 120:
            return val
    return 24  # Standard gaming gear warranty is 24 months

def normalize_brand(brand_raw: str, title: str) -> str:
    b = (brand_raw or "").strip()
    if not b or b.lower() in ["chưa rõ", "none", "đang cập nhật", "k"]:
        known = [
            "LOGITECH", "RAZER", "STEELSERIES", "HYPERX", "AKKO", "DAREU", "AULA",
            "LEOBOG", "LEOPOLD", "IKBC", "FUHLEN", "E-DRA", "EDRA", "ZOWIE", "PULSAR",
            "ENDGAME GEAR", "KEYCHRON", "FL-ESPORTS", "MONSGEEK", "SENNHEISER", "CORSAIR",
            "ASUS", "MSI", "GIGABYTE", "AOC", "SONY", "AUDIO TECHNICA", "JBL"
        ]
        for kb in known:
            if re.search(rf'\b{re.escape(kb)}\b', title, re.IGNORECASE):
                return kb
        return "Khác"
    
    brand_map = {
        "logitech": "Logitech", "razer": "Razer", "steelseries": "SteelSeries",
        "hyperx": "HyperX", "akko": "Akko", "dareu": "DareU", "e-dra": "E-Dra",
        "edra": "E-Dra", "fuhlen": "Fuhlen", "zowie": "Zowie", "aula": "Aula",
        "leobog": "Leobog", "leopold": "Leopold", "ikbc": "IKBC", "pulsar": "Pulsar",
        "keychron": "Keychron", "corsair": "Corsair", "asus": "ASUS", "msi": "MSI"
    }
    return brand_map.get(b.lower(), b.title())

def main():
    print("[*] Generating gear seed data for Keyboard, Mouse, and Headset...")

    # Load existing catalog_seed.json if available to reuse brand IDs and avoid conflicts
    existing_brands = {}
    existing_skus = set()
    existing_seos = set()
    existing_files = {}

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
    RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "gears")
    SEED_DIR = os.path.join(PROJECT_ROOT, "data", "seed")
    os.makedirs(SEED_DIR, exist_ok=True)

    cat_seed_path = os.path.join(SEED_DIR, "catalog_seed.json")
    if not os.path.exists(cat_seed_path):
        cat_seed_path = "catalog_seed.json"

    if os.path.exists(cat_seed_path):
        with open(cat_seed_path, "r", encoding="utf-8") as f:

            cat_seed = json.load(f)
            for b in cat_seed.get("brands", []):
                existing_brands[b["name"].lower()] = b
            for p in cat_seed.get("products", []):
                existing_seos.add(p["seo_name"])
            for pv in cat_seed.get("product_variants", []):
                existing_skus.add(pv["sku"])
            for fl in cat_seed.get("files", []):
                existing_files[fl["public_url"]] = fl

    new_brands = {}
    new_files = {}
    products = []
    product_variants = []
    product_images = []

    # Categories list according to user CTE
    categories = [
        {
            "id": cfg["id"],
            "name": cfg["name"],
            "seo_name": cfg["seo_name"],
            "hardware_type": cfg["hardware_type"],
            "description": f"Danh mục {cfg['name']}",
            "parent_id": None,
            "status": "ACTIVE"
        }
        for cfg in CATEGORY_CONFIG.values()
    ]

    sku_counter = 2000

    for cat_key, cfg in CATEGORY_CONFIG.items():
        json_file = os.path.join(RAW_DIR, cfg["file"])
        if not os.path.exists(json_file):
            json_file = cfg["file"]
        if not os.path.exists(json_file):
            print(f"[!] File not found: {json_file}, skipping.")
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        category_id = cfg["id"]
        cat_code = cfg["code"]
        print(f"[*] Processing {len(items)} items from {json_file}...")

        for item in items:
            raw_title = item.get("title", "").strip()
            if not raw_title:
                continue

            # --- BRAND ---
            brand_name = normalize_brand(item.get("brand"), raw_title)
            b_key = brand_name.lower()
            if b_key in existing_brands:
                brand_id = existing_brands[b_key]["id"]
            elif b_key in new_brands:
                brand_id = new_brands[b_key]["id"]
            else:
                brand_id = generate_uuidv7()
                brand_obj = {
                    "id": brand_id,
                    "name": brand_name,
                    "seo_name": slugify(brand_name),
                    "description": f"Thương hiệu {brand_name}",
                    "image_file_id": None,
                    "status": "ACTIVE"
                }
                new_brands[b_key] = brand_obj

            # --- PRODUCT ---
            product_id = generate_uuidv7()
            prod_name = raw_title[:255]

            base_seo = slugify(prod_name)[:200]
            prod_seo = base_seo
            idx = 2
            while prod_seo in existing_seos or not prod_seo:
                prod_seo = f"{base_seo[:190]}-{idx}"
                idx += 1
            existing_seos.add(prod_seo)

            specs = item.get("specs", {})

            products.append({
                "id": product_id,
                "name": prod_name,
                "seo_name": prod_seo,
                "brand_id": brand_id,
                "category_id": category_id,
                "specifications": specs,
                "description": f"Sản phẩm {prod_name}. Tham khảo chi tiết thông số kỹ thuật bên dưới.",
                "status": "ACTIVE",
                "created_by": SYSTEM_ADMIN_ID
            })

            # --- VARIANT ---
            variant_id = generate_uuidv7()
            sale_price = item.get("sale_price") or 0
            model = (item.get("model") or "").strip()[:100]

            clean_brand = re.sub(r'[^A-Z0-9]', '', brand_name.upper())[:4] or "GEAR"
            base_sku = f"{cat_code}-{clean_brand}-{sku_counter}"
            sku = base_sku
            while sku in existing_skus:
                sku_counter += 1
                sku = f"{cat_code}-{clean_brand}-{sku_counter}"
            existing_skus.add(sku)
            sku_counter += 1

            warranty_months = parse_warranty_months(item.get("warranty"), specs)
            stock_status = item.get("stock", "In Stock")
            is_active = (sale_price > 0) and ("out of stock" not in stock_status.lower())

            # --- IMAGES & FILES ---
            image_urls = item.get("images", [])
            main_image_file_id = None

            for img_idx, img_url in enumerate(image_urls):
                if not img_url:
                    continue

                if img_url in existing_files:
                    file_id = existing_files[img_url]["id"]
                elif img_url in new_files:
                    file_id = new_files[img_url]["id"]
                else:
                    file_id = generate_uuidv7()
                    f_name = os.path.basename(img_url.split('?')[0]) or "gear_image.png"
                    # clean storage key
                    clean_key = img_url.replace("https://pcmarket.vn/", "")
                    file_obj = {
                        "id": file_id,
                        "storage_provider": "EXTERNAL",
                        "storage_key": clean_key,
                        "original_name": f_name,
                        "mime_type": "image/jpeg" if f_name.endswith(('.jpg', '.jpeg')) else "image/png",
                        "size_bytes": 0,
                        "public_url": img_url,
                        "status": "ACTIVE"
                    }
                    new_files[img_url] = file_obj

                is_main = (img_idx == 0)
                if is_main:
                    main_image_file_id = file_id

                product_images.append({
                    "id": generate_uuidv7(),
                    "product_id": product_id,
                    "image_file_id": file_id,
                    "is_main": is_main
                })

            product_variants.append({
                "id": variant_id,
                "product_id": product_id,
                "price": sale_price,
                "quantity": 50 if is_active else 0,
                "sku": sku,
                "model": model if model else None,
                "image_file_id": main_image_file_id,
                "description": None,
                "warranty_months": warranty_months,
                "barcode": None,
                "release_at": None,
                "status": "ACTIVE" if is_active else "INACTIVE",
                "created_by": SYSTEM_ADMIN_ID
            })

    # Assemble standalone gear seed
    gear_seed = {
        "files": list(new_files.values()),
        "brands": list(new_brands.values()),
        "categories": categories,
        "products": products,
        "product_variants": product_variants,
        "product_images": product_images
    }

    out_file = os.path.join(SEED_DIR, "gear_catalog_seed.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(gear_seed, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print(f"[✓] Created {out_file} successfully!")
    print(f"    - Categories:     {len(categories)}")
    print(f"    - New Brands:     {len(new_brands)}")
    print(f"    - Products:       {len(products)}")
    print(f"    - Variants:       {len(product_variants)}")
    print(f"    - Product Images: {len(product_images)}")
    print(f"    - New Media Files:{len(new_files)}")
    print("="*60)

if __name__ == "__main__":
    main()
