#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Test pattern matching
potential_dish = "món mực"
main_ingredients = ["gà", "bò", "mực", "tôm", "cá", "heo", "thịt", "vịt", "cua", "ghẹ", "sò", "ốc", "tép", "trứng", "rau", "chay"]

print(f"Testing potential_dish: '{potential_dish}'")
print(f"potential_dish.lower(): '{potential_dish.lower()}'")

found_ingredient = None
for ing in main_ingredients:
    pattern = rf'\\b{ing}\\b'
    print(f"Testing ingredient '{ing}' with pattern '{pattern}'")
    if re.search(pattern, potential_dish.lower()):
        print(f"✅ MATCH: {ing}")
        found_ingredient = ing
        break
    else:
        print(f"❌ NO MATCH: {ing}")

print(f"\nResult: found_ingredient = {found_ingredient}")

# Test với pattern khác
print("\n=== TEST VỚI PATTERN ĐƠN GIẢN ===")
found_ingredient2 = None
for ing in main_ingredients:
    if ing in potential_dish.lower():
        print(f"✅ SIMPLE MATCH: {ing}")
        found_ingredient2 = ing
        break

print(f"Simple pattern result: {found_ingredient2}")
