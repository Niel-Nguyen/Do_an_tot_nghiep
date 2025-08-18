#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import difflib
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

dish_names = [dish.name for dish in dishes]
norm_dish_names = [normalize(name) for name in dish_names]

print("\n=== FUZZY MATCHING ANALYSIS ===")
matches = difflib.get_close_matches(user_norm, norm_dish_names, n=10, cutoff=0.6)

for match in matches:
    idx = norm_dish_names.index(match)
    similarity = difflib.SequenceMatcher(None, user_norm, match).ratio()
    print(f"Match: '{match}' -> {dish_names[idx]} (similarity: {similarity:.3f})")

print(f"\nTop match: {matches[0] if matches else 'None'}")

# Test với cutoff cao hơn
print("\n=== FUZZY MATCHING VỚI CUTOFF 0.8 ===")
matches_strict = difflib.get_close_matches(user_norm, norm_dish_names, n=5, cutoff=0.8)
for match in matches_strict:
    idx = norm_dish_names.index(match)
    similarity = difflib.SequenceMatcher(None, user_norm, match).ratio()
    print(f"Strict match: '{match}' -> {dish_names[idx]} (similarity: {similarity:.3f})")

print(f"\nStrict top match: {matches_strict[0] if matches_strict else 'None'}")
