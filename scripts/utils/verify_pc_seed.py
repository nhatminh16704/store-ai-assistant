import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

seed_path = os.path.join(os.path.dirname(__file__), "../../data/seed/pc_catalog_seed.json")
if not os.path.exists(seed_path):
    seed_path = "pc_catalog_seed.json"

with open(seed_path, 'r', encoding='utf-8') as f:
    seed = json.load(f)

variants = {v['id']: v for v in seed['product_variants']}
options = {o['id']: o for o in seed['options']}
products = {p['id']: p for p in seed['products']}
categories = {c['id']: c for c in seed['categories']}

print(f"Checking FKs and triggers for {len(seed['variant_options'])} variant_options...")

# 1. Foreign keys
for vo in seed['variant_options']:
    assert vo['product_variant_id'] in variants, f"Missing variant {vo['product_variant_id']}"
    assert vo['option_id'] in options, f"Missing option {vo['option_id']}"

# 2. Trigger check: check_variant_option_type_uniqueness
variant_option_names = {}
for vo in seed['variant_options']:
    v_id = vo['product_variant_id']
    o_name = options[vo['option_id']]['name'].strip().upper()
    if v_id not in variant_option_names:
        variant_option_names[v_id] = set()
    assert o_name not in variant_option_names[v_id], f"Variant {v_id} violated unique option type: {o_name}"
    variant_option_names[v_id].add(o_name)

# 3. Unique SKUs
skus = set()
for v in seed['product_variants']:
    sku = v['sku']
    assert sku not in skus, f"Duplicate SKU {sku}"
    skus.add(sku)

# 4. Unique SEO names
seos = set()
for p in seed['products']:
    seo = p['seo_name']
    assert seo not in seos, f"Duplicate SEO {seo}"
    seos.add(seo)

print("[✓] ALL DATABASE CONSTRAINTS & TRIGGERS PASSED PERFECTLY!")
print(f"Total Options:         {len(seed['options'])}")
print(f"Total Product Variants:{len(seed['product_variants'])}")
print(f"Total Variant Options: {len(seed['variant_options'])}")
if seed['options']:
    print(f"\nSample Option:         {seed['options'][0]}")
sample_var = seed['product_variants'][0]
print(f"Sample Variant:        SKU={sample_var['sku']}, Price={sample_var['price']:,}đ, Desc='{sample_var['description']}'")
if seed['variant_options']:
    print(f"Sample Variant Option: {seed['variant_options'][0]}")

