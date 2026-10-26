"""
Convert crawled PC part JSON datasets into structured Database Seed Data matching db.sql.
Exports to db_seed_data.json while preserving all original crawled files.
"""

import sys
import os
import re
import json
import time
import uuid
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

# Mock system employee / admin ID for audit trail fields (created_by)
SYSTEM_ADMIN_ID = "018f0000-0000-7000-8000-000000000001"

CATEGORY_METADATA = {
    "vga": {"name": "VGA - Card màn hình", "seo_name": "vga-card-man-hinh", "code": "VGA"},
    "cpu": {"name": "CPU - Bộ vi xử lý", "seo_name": "cpu-bo-vi-xu-ly", "code": "CPU"},
    "mainboard": {"name": "Mainboard - Bo mạch chủ", "seo_name": "mainboard-bo-mach-chu", "code": "MB"},
    "ram": {"name": "RAM - Bộ nhớ trong", "seo_name": "ram-bo-nho-trong", "code": "RAM"},
    "ssd": {"name": "Ổ cứng SSD", "seo_name": "o-cung-ssd", "code": "SSD"},
    "hdd": {"name": "Ổ cứng HDD", "seo_name": "o-cung-hdd", "code": "HDD"},
    "psu": {"name": "Nguồn máy tính - PSU", "seo_name": "psu-nguon-may-tinh", "code": "PSU"},
    "case": {"name": "Vỏ máy tính - Case", "seo_name": "case-vo-may-tinh", "code": "CASE"},
    "cooling": {"name": "Tản nhiệt - Cooling", "seo_name": "tan-nhiet-cooling", "code": "COOL"},
    "monitor": {"name": "Màn hình máy tính", "seo_name": "monitor-man-hinh", "code": "MON"},
    "keyboard": {"name": "Bàn phím chơi game", "seo_name": "ban-phim-choi-game", "code": "KB"},
    "mouse": {"name": "Chuột chơi game", "seo_name": "chuot-choi-game", "code": "MOU"},
    "headphone": {"name": "Tai nghe chơi game", "seo_name": "tai-nghe-choi-game", "code": "HP"},
}

def generate_uuidv7():
    """Generate RFC 9562 compliant UUIDv7."""
    ts_ms = int(time.time() * 1000)
    rand_bytes = bytearray(os.urandom(16))
    rand_bytes[0:6] = ts_ms.to_bytes(6, byteorder='big')
    rand_bytes[6] = (rand_bytes[6] & 0x0F) | 0x70  # Version 7
    rand_bytes[8] = (rand_bytes[8] & 0x3F) | 0x80  # Variant 1 (RFC 4122)
    return str(uuid.UUID(bytes=bytes(rand_bytes)))

def slugify(text: str) -> str:
    """Convert Vietnamese and special strings into safe URL slug."""
    text = unicodedata.normalize('NFKD', text)
    # replace Vietnamese d/D
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:200]

def parse_warranty_months(warranty_str, specs) -> int:
    """Extract warranty months as an integer (>0). Defaults to 36."""
    text = f"{warranty_str or ''} {specs.get('Bảo hành', '')} {specs.get('Thời gian bảo hành', '')}"
    match = re.search(r'(\d+)\s*(tháng|thang|m|months)', text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if 1 <= val <= 120:
            return val
    # Check years
    year_match = re.search(r'(\d+)\s*(năm|nam|years|yr)', text, re.IGNORECASE)
    if year_match:
        val = int(year_match.group(1)) * 12
        if 1 <= val <= 120:
            return val
    return 36

def normalize_brand(brand_raw: str, title: str) -> str:
    """Normalize brand name."""
    b = (brand_raw or "").strip()
    if not b or b.lower() in ["chưa rõ", "none", "đang cập nhật", "k"]:
        # Try inferring from title
        known = [
            "ASUS", "MSI", "GIGABYTE", "COLORFUL", "ZOTAC", "GALAX", "INNO3D", "PALIT",
            "SAPPHIRE", "LEADTEK", "INTEL", "AMD", "CORSAIR", "KINGSTON", "GSKILL",
            "SAMSUNG", "WESTERN DIGITAL", "SEAGATE", "COOLER MASTER", "NZXT", "XIGMATEK",
            "DEEPCOOL", "ID-COOLING", "THERMALRIGHT", "LIAN LI", "JONSBO", "SAMA", "MIK",
            "AOC", "LG", "DELL", "VIEWSONIC", "ACER", "PHILIPS", "HIKVISION", "DAHUA",
            "LOGITECH", "RAZER", "STEELSERIES", "HYPERX", "AKKO", "DAREU", "AULA",
            "LEOBOG", "LEOPOLD", "IKBC", "FUHLEN", "E-DRA", "EDRA", "ZOWIE", "PULSAR",
            "ENDGAME GEAR", "KEYCHRON", "FL-ESPORTS", "MONSGEEK", "SENNHEISER"
        ]
        for kb in known:
            if re.search(rf'\b{re.escape(kb)}\b', title, re.IGNORECASE):
                return kb
        return "Khác"
    
    # Standardize casing for common brands
    upper_map = {
        "msi": "MSI", "asus": "ASUS", "gigabyte": "GIGABYTE", "amd": "AMD",
        "intel": "Intel", "nzxt": "NZXT", "xigmatek": "Xigmatek", "corsair": "Corsair",
        "kingston": "Kingston", "samsung": "Samsung", "western digital": "Western Digital",
        "seagate": "Seagate", "colorful": "Colorful", "zotac": "ZOTAC", "galax": "GALAX",
        "inno3d": "INNO3D", "palit": "Palit", "sapphire": "Sapphire", "asrock": "ASRock",
        "logitech": "Logitech", "razer": "Razer", "steelseries": "SteelSeries", "hyperx": "HyperX",
        "akko": "Akko", "dareu": "DareU", "e-dra": "E-Dra", "fuhlen": "Fuhlen", "zowie": "Zowie"
    }
    return upper_map.get(b.lower(), b.title())

def main():
    print("[*] Starting conversion of crawled data to db.sql schema...")

    # Data collections for the DB
    brands_dict = {}          # name -> brand record
    categories_dict = {}      # cat_key -> category record
    files_dict = {}           # url -> file record
    products = []
    product_variants = []
    product_images = []

    # Track uniqueness for uk_products_seo_name and uk_product_variants_sku
    used_product_seo_names = set()
    used_skus = set()

    # 1. Initialize Categories
    for key, meta in CATEGORY_METADATA.items():
        cat_id = generate_uuidv7()
        categories_dict[key] = {
            "id": cat_id,
            "name": meta["name"],
            "seo_name": meta["seo_name"],
            "description": f"Danh mục linh kiện {meta['name']}",
            "parent_id": None,
            "status": "ACTIVE"
        }

    # 2. Iterate through each crawled JSON file
    total_raw_items = 0
    sku_counter = 1000

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
    RAW_COMP_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "components")
    RAW_GEAR_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "gears")
    SEED_DIR = os.path.join(PROJECT_ROOT, "data", "seed")
    os.makedirs(SEED_DIR, exist_ok=True)

    for cat_key, cat_meta in CATEGORY_METADATA.items():
        fname = f"{cat_key}_pcmarket.json"
        json_file = os.path.join(RAW_COMP_DIR, fname)
        if not os.path.exists(json_file):
            json_file = os.path.join(RAW_GEAR_DIR, fname)
        if not os.path.exists(json_file):
            json_file = fname
        if not os.path.exists(json_file):
            print(f"[!] File not found: {json_file}, skipping.")
            continue


        with open(json_file, 'r', encoding='utf-8') as f:
            items = json.load(f)

        category_id = categories_dict[cat_key]["id"]
        cat_code = cat_meta["code"]
        print(f"[*] Processing {len(items)} items from {json_file}...")
        total_raw_items += len(items)

        for item in items:
            raw_title = item.get("title", "").strip()
            if not raw_title:
                continue

            # --- BRAND ---
            brand_name = normalize_brand(item.get("brand"), raw_title)
            if brand_name not in brands_dict:
                b_slug = slugify(brand_name)
                # Ensure unique brand seo_name
                if any(b["seo_name"] == b_slug for b in brands_dict.values()):
                    b_slug = f"{b_slug}-{len(brands_dict)}"
                brands_dict[brand_name] = {
                    "id": generate_uuidv7(),
                    "name": brand_name,
                    "seo_name": b_slug,
                    "description": f"Thương hiệu linh kiện máy tính {brand_name}",
                    "image_file_id": None,
                    "status": "ACTIVE"
                }
            brand_id = brands_dict[brand_name]["id"]

            # --- PRODUCT ---
            product_id = generate_uuidv7()
            # Trim name to fit VARCHAR(255)
            prod_name = raw_title[:255]

            # Generate unique seo_name for product
            base_seo = slugify(prod_name)[:200]
            prod_seo = base_seo
            idx = 2
            while prod_seo in used_product_seo_names or not prod_seo:
                prod_seo = f"{base_seo[:190]}-{idx}"
                idx += 1
            used_product_seo_names.add(prod_seo)

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

            # --- PRODUCT VARIANT ---
            variant_id = generate_uuidv7()
            sale_price = item.get("sale_price") or 0
            model = (item.get("model") or "").strip()[:100]

            # Generate unique SKU: {CAT_CODE}-{BRAND[:3]}-{NUMBER}
            clean_brand = re.sub(r'[^A-Z0-9]', '', brand_name.upper())[:4] or "GEN"
            base_sku = f"{cat_code}-{clean_brand}-{sku_counter}"
            sku = base_sku
            while sku in used_skus:
                sku_counter += 1
                sku = f"{cat_code}-{clean_brand}-{sku_counter}"
            used_skus.add(sku)
            sku_counter += 1

            warranty_months = parse_warranty_months(item.get("warranty"), specs)
            stock_status = item.get("stock", "In Stock")
            is_active = (sale_price > 0) and ("out of stock" not in stock_status.lower())

            # --- IMAGES (Media Service: files & product_images) ---
            image_urls = item.get("images", [])
            main_image_file_id = None

            for img_idx, img_url in enumerate(image_urls):
                if not img_url:
                    continue
                # Create file record if not exists
                if img_url not in files_dict:
                    f_id = generate_uuidv7()
                    f_name = os.path.basename(img_url.split('?')[0]) or "product_image.png"
                    files_dict[img_url] = {
                        "id": f_id,
                        "storage_provider": "EXTERNAL_URL",
                        "storage_key": img_url,
                        "original_name": f_name,
                        "mime_type": "image/jpeg" if f_name.endswith(('.jpg', '.jpeg')) else "image/png",
                        "size_bytes": 0,
                        "public_url": img_url,
                        "status": "ACTIVE"
                    }
                file_id = files_dict[img_url]["id"]

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

    # Assemble complete database seed package
    output_data = {
        "meta": {
            "description": "Database Seed Data conforming to db.sql Catalog & Media Services",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_categories": len(categories_dict),
            "total_brands": len(brands_dict),
            "total_products": len(products),
            "total_variants": len(product_variants),
            "total_media_files": len(files_dict),
            "total_product_images": len(product_images)
        },
        "brands": list(brands_dict.values()),
        "categories": list(categories_dict.values()),
        "products": products,
        "product_variants": product_variants,
        "product_images": product_images,
        "files": list(files_dict.values())
    }

    out_file = os.path.join(SEED_DIR, "db_seed_data.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


    print("\n" + "=" * 60)
    print(f"[✓] Successfully created {out_file}!")
    print(f"    - Categories:     {len(categories_dict)}")
    print(f"    - Brands:         {len(brands_dict)}")
    print(f"    - Products:       {len(products):,}")
    print(f"    - Variants:       {len(product_variants):,}")
    print(f"    - Media Files:    {len(files_dict):,}")
    print(f"    - Product Images: {len(product_images):,}")
    print(f"    - File Size:      {round(os.path.getsize(out_file) / (1024*1024), 2)} MB")
    print("=" * 60)

if __name__ == "__main__":
    main()
