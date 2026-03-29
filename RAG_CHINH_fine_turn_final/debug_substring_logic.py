#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Debug logic substring matching
import re
import unicodedata

def normalize(text):
    if not text:
        return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Load dishes
from utils.excel_loader import load_dishes_from_excel
import os

data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
dishes = load_dishes_from_excel(data_path)

user_input = "món nào có gà"
user_norm = normalize(user_input)
print(f"user_norm: '{user_norm}'")

print("\n=== KIỂM TRA SUBSTRING MATCHING ===")
for dish in dishes:
    dish_norm = normalize(dish.name)
    if dish_norm in user_norm:
        print(f"✅ MATCH: '{dish_norm}' IN '{user_norm}' -> {dish.name}")
    elif any(word in user_norm for word in dish_norm.split() if len(word) > 2):
        words_matched = [word for word in dish_norm.split() if len(word) > 2 and word in user_norm]
        print(f"⚠️  PARTIAL: {words_matched} -> {dish.name}")

print("\n=== KIỂM TRA FUZZY MATCHING ===")
dish_names = [dish.name for dish in dishes]
norm_dish_names = [normalize(name) for name in dish_names]

import difflib
matches = difflib.get_close_matches(user_norm, norm_dish_names, n=5, cutoff=0.6)
for match in matches:
    idx = norm_dish_names.index(match)
    similarity = difflib.SequenceMatcher(None, user_norm, match).ratio()
    print(f"Fuzzy match: '{match}' (similarity: {similarity:.2f}) -> {dish_names[idx]}")

print("\n=== KIỂM TRA KEYWORD MATCHING ===")
for dish in dishes:
    dish_norm = normalize(dish.name)
    keywords = [w for w in dish_norm.split() if len(w) > 1]
    if all(kw in user_norm for kw in keywords):
        print(f"✅ ALL KEYWORDS MATCH: {keywords} -> {dish.name}")
