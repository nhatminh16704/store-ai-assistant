# PCMarket.vn Web Crawler for PC Parts

A robust, production-ready crawler designed to scrape PC parts and hardware from **pcmarket.vn**.

## Features

- **Detailed Data Extraction**:
  - Title, Product URL, Brand, Model
  - Sale Price, Market Price, Discount Percentage
  - Warranty period & Stock / Availability status
  - Breadcrumb navigation path
  - Full Technical Specifications table (parsed as key-value pairs)
  - High-resolution gallery images (strips thumbnail prefixes)
- **Flexible Crawling**:
  - Single product page crawl
  - Category page crawl with multi-page pagination support
  - Built-in category shortcodes (`vga`, `cpu`, `mainboard`, `ram`, `ssd`, `hdd`, `psu`, `case`, `cooling`, `monitor`)
- **Multi-Format Export**:
  - **JSON**: Preserves nested technical specifications and full image arrays.
  - **CSV**: UTF-8 with BOM for Vietnamese character support in Excel.
  - **Excel (`.xlsx`)**: Flattened table with dynamic columns for each technical spec.

---

## Requirements & Setup

Dependencies (`requests`, `beautifulsoup4`, `lxml`, `pandas`, `openpyxl`):

```bash
pip install requests beautifulsoup4 lxml pandas openpyxl
```

---

## Usage Examples

### 1. Crawl a Single Product

```bash
python crawler.py --url https://pcmarket.vn/card-man-hinh-asus-rog-astral-geforce-rtx-5090-edition-20 --out single_product
```

### 2. Crawl a Category by Shortcode (e.g., VGA)

Crawl page 1 of VGA products:
```bash
python crawler.py --category vga --pages 1 --out vga_page1
```

Crawl 5 pages of CPUs with a limit of 50 items:
```bash
python crawler.py --category cpu --pages 5 --max-items 50 --out cpu_parts
```

### 3. Crawl Any Category by Direct URL

```bash
python crawler.py --category https://pcmarket.vn/mainboard-bo-mach-chu.html --pages 2 --out mainboards
```

---

## CLI Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | Direct URL of a single product to scrape | None |
| `--category` | Category shortcode or full category URL | None |
| `--pages` | Maximum number of pagination pages to traverse | `1` |
| `--max-items` | Limit total number of products to crawl | None (All) |
| `--delay` | Delay in seconds between requests (politeness delay) | `0.5` |
| `--out` | Output file basename (without extension) | `pcmarket_data` |

---

## Supported Category Shortcodes

- `vga`: `https://pcmarket.vn/vga-card-man-hinh.html`
- `cpu`: `https://pcmarket.vn/cpu-bo-vi-xu-ly.html`
- `mainboard`: `https://pcmarket.vn/mainboard-bo-mach-chu.html`
- `ram`: `https://pcmarket.vn/ram-bo-nho-trong.html`
- `ssd`: `https://pcmarket.vn/o-cung-ssd.html`
- `hdd`: `https://pcmarket.vn/o-cung-hdd.html`
- `psu`: `https://pcmarket.vn/psu-nguon-may-tinh.html`
- `case`: `https://pcmarket.vn/case-vo-may-tinh.html`
- `cooling`: `https://pcmarket.vn/tan-nhiet-cooling.html`
- `monitor`: `https://pcmarket.vn/monitor-man-hinh.html`
