#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import unicodedata

def normalize_temp(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

# Test với câu hỏi về gà
potential_dish = "món nào có gà"
main_ingredients = ["gà", "bò", "mực", "tôm", "cá", "heo", "thịt", "vịt", "cua", "ghẹ", "sò", "ốc", "tép", "trứng", "rau", "chay"]

print(f"Testing potential_dish: '{potential_dish}'")

found_ingredient = None
for ing in main_ingredients:
    pattern = rf'\b{ing}\b'
    print(f"Testing ingredient '{ing}' with pattern '{pattern}'")
    if re.search(pattern, potential_dish.lower()):
        print(f"✅ MATCH: {ing}")
        found_ingredient = ing
        break
    else:
        print(f"❌ NO MATCH: {ing}")

print(f"\nFound ingredient: {found_ingredient}")

# Test với danh sách món mẫu
sample_dishes = [
    "Mực ống hấp củ đậu",
    "Gà nướng lá hương liu",
    "Chảo gà lá quế",
    "Canh gà hạt lựu"
]

if found_ingredient:
    found_ingredient_norm = normalize_temp(found_ingredient)
    print(f"\nNormalized ingredient: '{found_ingredient_norm}'")
    
    matched_dishes = []
    for dish_name in sample_dishes:
        dish_norm = normalize_temp(dish_name)
        print(f"Checking dish: '{dish_name}' -> normalized: '{dish_norm}'")
        if found_ingredient_norm in dish_norm:
            print(f"  ✅ CONTAINS '{found_ingredient_norm}': TRUE")
            matched_dishes.append(dish_name)
        else:
            print(f"  ❌ CONTAINS '{found_ingredient_norm}': FALSE")
    
    print(f"\nMatched dishes: {matched_dishes}")
else:
    print("No ingredient found!")
