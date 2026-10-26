# Store AI Assistant - E-Commerce Hardware & PC Catalog

Dữ liệu sản phẩm linh kiện máy tính, Gaming Gear và máy tính nguyên bộ (Pre-built PC) được crawl từ `pcmarket.vn`, chuẩn hoá theo mô hình Microservices Postgres Database Schema ([db.sql](file:///e:/Temp/ecom-pcpart/sql/db.sql)) với UUIDv7 và cây danh mục chuẩn.

---

## 📁 Cấu trúc thư mục dự án

```text
ecom-pcpart/
├── data/
│   ├── raw/                              # Dữ liệu gốc sau khi crawl
│   │   ├── components/                   # 10 danh mục linh kiện phần cứng (CPU, VGA, Mainboard...)
│   │   │   ├── cpu_pcmarket.json
│   │   │   ├── mainboard_pcmarket.json
│   │   │   ├── ram_pcmarket.json
│   │   │   ├── vga_pcmarket.json
│   │   │   ├── psu_pcmarket.json
│   │   │   ├── case_pcmarket.json
│   │   │   ├── cooling_pcmarket.json
│   │   │   ├── ssd_pcmarket.json
│   │   │   ├── hdd_pcmarket.json
│   │   │   └── monitor_pcmarket.json
│   │   ├── gears/                        # Gaming Gear (Bàn phím, Chuột, Tai nghe)
│   │   │   ├── keyboard_pcmarket.json
│   │   │   ├── mouse_pcmarket.json
│   │   │   └── headphone_pcmarket.json
│   │   └── pc_builds/                    # 5 phân khúc máy tính dựng sẵn (Pre-built PC)
│   │       ├── pc_builds_pcmarket.json   # Tổng hợp 591 bộ PC
│   │       ├── pc_gaming_pcmarket.json
│   │       ├── pc_workstation_pcmarket.json
│   │       ├── pc_office_pcmarket.json
│   │       ├── pc_ai_pcmarket.json
│   │       └── pc_mini_pcmarket.json
│   └── seed/                             # Dữ liệu Seed chuẩn hoá để nạp Database
│       ├── catalog_seed.json             # Seed cho Hardware + Gaming Gear
│       ├── pc_catalog_seed.json          # Seed 591 bộ PC (Cấu hình chuẩn 1:1)
│       ├── gear_catalog_seed.json        # Seed riêng Gaming Gear
│       └── db_seed_data.json             # Seed tổng hợp toàn bộ linh kiện
├── scripts/
│   ├── crawlers/                         # Các script cào dữ liệu
│   │   ├── crawler.py                    # Core crawler đa luồng
│   │   ├── crawl_all_parts.py            # Quét 10 danh mục linh kiện
│   │   ├── crawl_gears.py                # Quét bàn phím, chuột, tai nghe
│   │   └── crawl_pc_builds.py            # Quét 5 danh mục PC nguyên bộ
│   ├── generators/                       # Scripts chuyển đổi & chuẩn hoá seed
│   │   ├── convert_to_db_json.py         # Build db_seed_data.json & catalog_seed.json
│   │   ├── generate_gear_seed.py         # Build gear_catalog_seed.json
│   │   └── generate_pc_seed.py           # Build pc_catalog_seed.json (591 PCs)
│   └── utils/
│       ├── stats.py                      # Thống kê số lượng, dung lượng, khoảng giá
│       └── verify_pc_seed.py             # Kiểm tra ràng buộc khóa ngoại & trigger DB
├── sql/
│   ├── db.sql                            # Schema DDL (Identity, Catalog, Media)
│   ├── seed_data.sql                     # SQL insert mẫu
│   └── specs_normalized.sql              # SQL tham chiếu danh mục & chuẩn hoá specs
├── README.md
└── .gitignore
```

---

## 📊 Thống kê dữ liệu đã thu thập

| Danh mục | Số sản phẩm | Khoảng giá (VND) |
| :--- | :---: | :--- |
| **VGA (Card màn hình)** | 358 | 1,090,000 đ - 269,990,000 đ |
| **Mainboard (Bo mạch chủ)** | 284 | 1,450,000 đ - 99,990,000 đ |
| **Vỏ case** | 260 | 290,000 đ - 94,990,000 đ |
| **Tản nhiệt (Cooling)** | 194 | 79,000 đ - 10,990,000 đ |
| **Màn hình** | 172 | 1,390,000 đ - 50,460,000 đ |
| **CPU (Bộ vi xử lý)** | 126 | 1,690,000 đ - 28,990,000 đ |
| **Nguồn (PSU)** | 113 | 450,000 đ - 29,900,000 đ |
| **RAM** | 63 | 1,790,000 đ - 69,990,000 đ |
| **Ổ cứng SSD** | 45 | 1,190,000 đ - 37,999,000 đ |
| **Ổ cứng HDD** | 10 | 3,790,000 đ - 10,290,000 đ |
| **Bàn phím** | 90 | 300,000 đ - 19,990,000 đ |
| **Chuột** | 52 | 49,000 đ - 8,990,000 đ |
| **Tai nghe** | 31 | 290,000 đ - 4,990,000 đ |
| **PC Dựng sẵn (Pre-built PC)** | 591 | 6,680,000 đ - 532,000,000 đ |
| **TỔNG CỘNG** | **2,389 sản phẩm** | **100% hình ảnh & specs sạch** |

---

## ⚙️ Chuẩn hoá Dữ liệu & Schema Database

1. **UUIDv7:** Tất cả ID (`products`, `categories`, `brands`, `product_variants`, `files`) đều tạo bằng RFC 9562 UUIDv7 tuần tự theo thời gian.
2. **Cây danh mục máy tính dựng sẵn (Category Hierarchy):**
   - Danh mục cha: `Máy tính để bàn` (`parent_id = NULL`)
   - 5 Danh mục con: `PC Gaming`, `PC Workstation`, `PC Văn phòng`, `PC AI`, `PC Mini` trỏ `parent_id` về danh mục cha.
3. **Quản lý Variant thực tế (1 Product = 1 Base Variant):**
   - 591 bộ PC được quản lý bằng đúng 591 Variant cấu hình tiêu chuẩn chính hãng.
   - Tránh việc nhân tổ hợp làm phình to database (từng tạo hơn 4,000 variants không cần thiết).
4. **Thông số kỹ thuật (`specifications`):**
   - Các key được ánh xạ sạch sẽ về 9 loại linh kiện chuẩn: `CPU`, `MAINBOARD`, `RAM`, `GPU`, `STORAGE`, `PSU`, `CASE`, `COOLER`, `MONITOR`.
