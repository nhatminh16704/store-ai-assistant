"""
Generate seed JSON for Pre-built PC sets matching catalog_seed.json structure.
Implements:
1. Category hierarchy:
   - Parent Category: 'Máy tính để bàn', seo_name='pc', hardware_type='PREBUILT_PC', parent_id=None
   - 5 Child Categories (parent_id -> Parent Category ID):
     * 'PC Gaming', seo_name='pc-gaming', hardware_type='PC_GAMING'
     * 'PC Workstation', seo_name='pc-workstation', hardware_type='PC_WORKSTATION'
     * 'PC Văn phòng', seo_name='pc-office', hardware_type='PC_OFFICE'
     * 'PC AI', seo_name='pc-ai', hardware_type='PC_AI'
     * 'PC Mini', seo_name='pc-mini', hardware_type='PC_MINI'
2. Normalized specifications keys matching canonical hardware_types:
   - CPU, MAINBOARD, RAM, GPU, STORAGE, PSU, CASE, COOLER, MONITOR
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
PARENT_PC_CATEGORY_ID = "01a18888-0000-7000-8000-000000000001"

PC_CHILD_CATEGORIES = {
    "pc_gaming": {
        "id": "01a18888-0001-7000-8000-000000000001",
        "name": "PC Gaming",
        "seo_name": "pc-gaming",
        "hardware_type": "PC_GAMING",
        "code": "PCG",
        "file": "pc_gaming_pcmarket.json",
        "description": "Máy tính chơi game, livestream hiệu năng cao"
    },
    "pc_workstation": {
        "id": "01a18888-0002-7000-8000-000000000002",
        "name": "PC Workstation",
        "seo_name": "pc-workstation",
        "hardware_type": "PC_WORKSTATION",
        "code": "PCW",
        "file": "pc_workstation_pcmarket.json",
        "description": "Máy tính đồ họa 3D, kiến trúc, render video"
    },
    "pc_office": {
        "id": "01a18888-0003-7000-8000-000000000003",
        "name": "PC Văn phòng",
        "seo_name": "pc-office",
        "hardware_type": "PC_OFFICE",
        "code": "PCO",
        "file": "pc_office_pcmarket.json",
        "description": "Máy tính văn phòng, kế toán, thu ngân, doanh nghiệp"
    },
    "pc_ai": {
        "id": "01a18888-0004-7000-8000-000000000004",
        "name": "PC AI",
        "seo_name": "pc-ai",
        "hardware_type": "PC_AI",
        "code": "PCAI",
        "file": "pc_ai_pcmarket.json",
        "description": "Máy tính trí tuệ nhân tạo, training & inference AI"
    },
    "pc_mini": {
        "id": "01a18888-0005-7000-8000-000000000005",
        "name": "PC Mini",
        "seo_name": "pc-mini",
        "hardware_type": "PC_MINI",
        "code": "PCMINI",
        "file": "pc_mini_pcmarket.json",
        "description": "Máy tính nhỏ gọn Mini ITX, tiết kiệm không gian"
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
    return 36

def normalize_pc_specs(raw_specs: dict) -> dict:
    """
    Normalize raw component keys into canonical hardware_types:
    CPU, MAINBOARD, RAM, GPU, STORAGE, PSU, CASE, COOLER, MONITOR
    Filters out web radio button upgrade options (e.g. 'RAM 16GB DDR5Ram 32GB DDR5').
    """
    real_components = []
    fallback_components = []

    for k, v in raw_specs.items():
        if not v or not isinstance(v, str):
            continue
        v_clean = v.strip()

        # Filter out concatenated button labels from web UI
        if any(v_clean.startswith(prefix) for prefix in [
            'Ram 16GB DDR4Ram', 'RAM 16GB DDR5Ram', 'RAM 8GBRAM', 'RAM 32GBRAM',
            'SSD 500GBSSD', 'SSD 256GBSSD', 'SSD 512GBSSD', 'SSD 1TBSSD',
            'Tản nhiệt khíTản', 'Tản nhiệt KhíTản', 'Windows Dùng ThửWindows',
            'ULTRA 7 265KFULTRA', 'ULTRA 5 245KULTRA', 'ULTRA 9 285KULTRA'
        ]):
            continue

        if '(SL:' in v_clean or 'BH:' in v_clean:
            real_components.append((k, v_clean))
        else:
            fallback_components.append((k, v_clean))

    # Prioritize official components from the breakdown table
    items_to_process = real_components if real_components else fallback_components

    norm = {}
    for k, v in items_to_process:
        kl = k.lower()
        vl = v.lower()

        if any(w in kl for w in ['cpu', 'vi xử lý', 'bộ vi xử lý']) or any(w in vl for w in ['cpu ', 'ryzen', 'core i', 'core ultra', 'intel core', 'xeon', 'athlon']):
            target = "CPU"
        elif any(w in kl for w in ['mainboard', 'bo mạch', 'main']) or any(w in vl for w in ['mainboard', 'bo mạch', 'a520', 'b760', 'b650', 'z790', 'z890', 'h610', 'b550', 'b860']):
            target = "MAINBOARD"
        elif any(w in kl for w in ['ram', 'bộ nhớ']) or any(w in vl for w in ['ram ', 'ddr4', 'ddr5']):
            target = "RAM"
        elif any(w in kl for w in ['vga', 'card màn hình', 'đồ họa']) or any(w in vl for w in ['vga', 'rtx', 'gtx', 'radeon', 'geforce', 'card ']):
            target = "GPU"
        elif any(w in kl for w in ['ổ cứng', 'ssd', 'hdd', 'rom']) or any(w in vl for w in ['ssd', 'nvme', 'm.2', 'sata 3', 'hdd']):
            target = "STORAGE"
        elif any(w in kl for w in ['nguồn', 'psu']) or any(w in vl for w in ['nguồn máy tính', 'nguồn ', 'psu ']):
            target = "PSU"
        elif any(w in kl for w in ['case', 'vỏ', 'thùng máy']) or any(w in vl for w in ['vỏ case', 'vỏ ', 'case ']):
            target = "CASE"
        elif any(w in kl for w in ['tản', 'cooler', 'cooling', 'aio', 'quạt']) or any(w in vl for w in ['tản nhiệt', 'cooler', 'aio ']):
            target = "COOLER"
        elif any(w in kl for w in ['màn hình', 'monitor', 'display']):
            target = "MONITOR"
        else:
            continue

        if target not in norm:
            norm[target] = v
        elif norm[target] != v and ('ssd' in v.lower() or 'hdd' in v.lower() or 'ram' in v.lower()):
            # Only add _2 if genuinely a secondary drive or separate secondary kit
            norm[f"{target}_2"] = v

    return norm

def normalize_pc_brand(brand_raw: str, title: str) -> str:
    tl = title.lower()
    if 'rog' in tl or 'asus' in tl or 'tuf' in tl:
        return "ASUS"
    elif 'msi' in tl:
        return "MSI"
    elif 'aorus' in tl or 'gigabyte' in tl:
        return "GIGABYTE"
    elif 'colorful' in tl or 'igame' in tl:
        return "Colorful"
    elif 'nzxt' in tl:
        return "NZXT"
    elif 'corsair' in tl:
        return "Corsair"
    elif 'dell' in tl:
        return "Dell"
    elif 'hp' in tl:
        return "HP"
    elif 'lenovo' in tl:
        return "Lenovo"
    elif brand_raw and brand_raw.strip().lower() not in ['chưa rõ', 'none', 'đang cập nhật']:
        return brand_raw.strip().title()
    return "PCM"

def main():
    print("[*] Generating Pre-built PC Seed data matching catalog_seed schema...")

    existing_brands = {}
    existing_skus = set()
    existing_seos = set()
    existing_files = {}

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
    RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "pc_builds")
    SEED_DIR = os.path.join(PROJECT_ROOT, "data", "seed")
    os.makedirs(SEED_DIR, exist_ok=True)

    # Load existing catalog_seed.json to ensure uniqueness and reuse IDs
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


    used_brands = {}
    new_files = {}
    products = []
    product_variants = []
    product_images = []
    options_map = {} # (name, value) -> dict
    variant_options = []


    # 1. Build Categories Hierarchy (Parent + 5 Children)
    categories = [
        {
            "id": PARENT_PC_CATEGORY_ID,
            "name": "Máy tính để bàn",
            "seo_name": "pc",
            "hardware_type": "PREBUILT_PC",
            "description": "Máy tính để bàn dựng sẵn, PC đồng bộ chính hãng",
            "parent_id": None,
            "status": "ACTIVE"
        }
    ]

    for cfg in PC_CHILD_CATEGORIES.values():
        categories.append({
            "id": cfg["id"],
            "name": cfg["name"],
            "seo_name": cfg["seo_name"],
            "hardware_type": cfg["hardware_type"],
            "description": cfg["description"],
            "parent_id": PARENT_PC_CATEGORY_ID,
            "status": "ACTIVE"
        })

    def parse_product_options(specs):
        opts = {}
        for k, v in specs.items():
            if '(SL:' in v or 'BH:' in v:
                continue
            kl = k.lower()
            vl = v.lower()
            if 'ram' in kl:
                if '16gb ddr4' in vl and '32gb ddr4' in vl:
                    opts['RAM'] = [('16GB DDR4', 0), ('32GB DDR4', 750000)]
                elif '16gb ddr5' in vl and '32gb ddr5' in vl:
                    opts['RAM'] = [('16GB DDR5', 0), ('32GB DDR5', 1100000)]
                elif '32gb ddr5' in vl and '64gb ddr5' in vl:
                    opts['RAM'] = [('32GB DDR5', 0), ('64GB DDR5', 2200000)]
                elif '8gb' in vl and '16gb' in vl:
                    opts['RAM'] = [('8GB DDR4', 0), ('16GB DDR4', 450000)]
            elif 'ssd' in kl or 'ổ cứng' in kl:
                if '256gb' in vl and '500gb' in vl:
                    opts['Ổ cứng SSD'] = [('SSD 256GB', 0), ('SSD 500GB', 350000)]
                elif '256gb' in vl and '512gb' in vl:
                    opts['Ổ cứng SSD'] = [('SSD 256GB', 0), ('SSD 512GB NVMe', 400000), ('SSD 1TB NVMe', 900000)]
                elif '500gb' in vl and '1tb' in vl:
                    opts['Ổ cứng SSD'] = [('SSD 500GB', 0), ('SSD 1TB', 800000)]
                elif '512gb' in vl and '1tb' in vl:
                    opts['Ổ cứng SSD'] = [('SSD 512GB', 0), ('SSD 1TB', 800000)]
            elif 'tản' in kl or 'cooler' in kl:
                if 'khí' in vl and 'aio 240' in vl:
                    opts['Tản nhiệt'] = [('Tản nhiệt khí', 0), ('Tản nhiệt nước AIO 240', 650000)]
                elif 'khí' in vl and 'aio 360' in vl:
                    opts['Tản nhiệt'] = [('Tản nhiệt khí', 0), ('Tản nhiệt nước AIO 360', 1200000)]
            elif 'cpu' in kl:
                if '13400f' in vl and '12600kf' in vl:
                    opts['CPU'] = [('Core i5 13400F', 0), ('Core i5 12600KF', 600000)]
                elif '14900kf' in vl and '14900k' in vl:
                    opts['CPU'] = [('Core i9 14900KF', 0), ('Core i9 14900K', 500000)]
                elif '7500f' in vl and '7600x' in vl:
                    opts['CPU'] = [('Ryzen 5 7500F', 0), ('Ryzen 5 7600X', 800000), ('Ryzen 7 7700', 1600000)]
                elif '265kf' in vl and '265k' in vl:
                    opts['CPU'] = [('Ultra 7 265KF', 0), ('Ultra 7 265K', 600000)]
                elif '12400f' in vl and '13400f' in vl and '14400f' in vl:
                    opts['CPU'] = [('Core i5 12400F', 0), ('Core i5 13400F', 900000), ('Core i5 12600KF', 1500000), ('Core i5 14400F', 1800000)]
                elif '12400f' in vl and '13400f' in vl:
                    opts['CPU'] = [('Core i5 12400F', 0), ('Core i5 13400F', 900000), ('Core i5 12600KF', 1500000)]
        return opts

    def get_or_create_option(opt_name: str, opt_val: str) -> str:
        key = (opt_name.strip(), opt_val.strip())
        if key not in options_map:
            opt_id = generate_uuidv7()
            options_map[key] = {
                "id": opt_id,
                "name": opt_name.strip(),
                "value": opt_val.strip(),
                "created_at": "2026-03-31T00:00:00Z"
            }
        return options_map[key]["id"]

    sku_counter = 3000

    # 2. Iterate through each pre-built PC category
    for cat_key, cfg in PC_CHILD_CATEGORIES.items():
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
        print(f"[*] Processing {len(items)} pre-built PCs from {json_file}...")

        for item in items:
            raw_title = item.get("title", "").strip()
            if not raw_title:
                continue

            # Brand
            brand_name = normalize_pc_brand(item.get("brand"), raw_title)
            b_key = brand_name.lower()
            if b_key in existing_brands:
                brand_obj = existing_brands[b_key]
            else:
                brand_obj = {
                    "id": generate_uuidv7(),
                    "name": brand_name,
                    "seo_name": slugify(brand_name),
                    "description": f"Thương hiệu máy tính {brand_name}",
                    "image_file_id": None,
                    "status": "ACTIVE"
                }
                existing_brands[b_key] = brand_obj

            brand_id = brand_obj["id"]
            used_brands[brand_id] = brand_obj

            # Product
            product_id = generate_uuidv7()
            prod_name = raw_title[:255]

            base_seo = slugify(prod_name)[:200]
            prod_seo = base_seo
            idx = 2
            while prod_seo in existing_seos or not prod_seo:
                prod_seo = f"{base_seo[:190]}-{idx}"
                idx += 1
            existing_seos.add(prod_seo)

            # Normalized Specifications matching hardware_types
            raw_specs = item.get("specs", {})
            norm_specs = normalize_pc_specs(raw_specs)

            products.append({
                "id": product_id,
                "name": prod_name,
                "seo_name": prod_seo,
                "brand_id": brand_id,
                "category_id": category_id,
                "specifications": norm_specs,
                "description": f"Bộ máy tính {prod_name}. Cấu hình chi tiết các linh kiện bên trong được liệt kê đầy đủ trong phần thông số kỹ thuật.",
                "status": "ACTIVE",
                "created_by": SYSTEM_ADMIN_ID
            })

            # Base properties
            sale_price = item.get("sale_price") or 0
            model = (item.get("model") or "").strip()[:100]
            clean_brand = re.sub(r'[^A-Z0-9]', '', brand_name.upper())[:4] or "PC"
            sku_prefix = f"{cat_code}-{clean_brand}-{sku_counter}"
            sku_counter += 1

            warranty_months = parse_warranty_months(item.get("warranty"), raw_specs)
            stock_status = item.get("stock", "In Stock")
            is_active = (sale_price > 0) and ("out of stock" not in stock_status.lower())

            # Images & Files
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
                    f_name = os.path.basename(img_url.split('?')[0]) or "pc_image.png"
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

            # Single Clean Base Variant per PC (Official Store Configuration)
            var_sku = f"{sku_prefix}"
            while var_sku in existing_skus:
                var_sku = f"{sku_prefix}-{idx}"
                idx += 1
            existing_skus.add(var_sku)

            product_variants.append({
                "id": generate_uuidv7(),
                "product_id": product_id,
                "price": sale_price,
                "quantity": 20 if is_active else 0,
                "sku": var_sku,
                "model": model if model else None,
                "image_file_id": main_image_file_id,
                "description": "Cấu hình tiêu chuẩn chính hãng",
                "warranty_months": warranty_months,
                "barcode": None,
                "release_at": None,
                "status": "ACTIVE" if is_active else "INACTIVE",
                "created_by": SYSTEM_ADMIN_ID
            })

    output_seed = {
        "files": list(new_files.values()),
        "brands": list(used_brands.values()),
        "categories": categories,
        "products": products,
        "options": [],
        "product_variants": product_variants,
        "variant_options": [],
        "product_images": product_images
    }

    out_file = os.path.join(SEED_DIR, "pc_catalog_seed.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_seed, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print(f"[✓] Created {out_file} successfully!")
    print(f"    - Categories:      {len(categories)} (1 Parent + 5 Children)")
    print(f"    - Brands:          {len(used_brands)}")
    print(f"    - Pre-built PCs:   {len(products)}")
    print(f"    - Product Variants:{len(product_variants)}")
    print(f"    - Product Images:  {len(product_images)}")
    print(f"    - New Media Files: {len(new_files)}")
    print("="*60)


if __name__ == "__main__":
    main()

