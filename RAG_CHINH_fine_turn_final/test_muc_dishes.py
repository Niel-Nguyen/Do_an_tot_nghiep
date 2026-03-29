#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copy hàm normalize từ chatbot.py
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

# Test các món mực
from utils.excel_loader import load_dishes_from_excel
import os

print("=== KIỂM TRA CÁC MÓN MỰC ===")

# Load dữ liệu
data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
dishes = load_dishes_from_excel(data_path)

print(f"Tổng số món trong Excel: {len(dishes)}")

# Tìm các món có chứa từ mực
muc_dishes = []
for dish in dishes:
    dish_name_norm = normalize(dish.name)
    if 'muc' in dish_name_norm:
        muc_dishes.append(dish)
        print(f"✓ [{dish.name}] -> normalized: [{dish_name_norm}]")

print(f"\nTổng cộng: {len(muc_dishes)} món mực tìm thấy")

# Test cụ thể với từ khóa "mực"
print("\n=== TEST TÌM KIẾM VỚI TỪ KHÓA 'mực' ===")
query = "mực"
query_norm = normalize(query)
print(f"Query normalized: [{query_norm}]")

# Kiểm tra logic tìm kiếm tương tự như trong chatbot
found_dishes = []
for dish in dishes:
    dish_name_norm = normalize(dish.name)
    if query_norm in dish_name_norm:
        found_dishes.append(dish)
        print(f"✓ Match: [{dish.name}]")

print(f"\nKết quả tìm kiếm: {len(found_dishes)} món")

if len(found_dishes) == 0:
    print("❌ KHÔNG TÌM THẤY MÚC - CÓ VẤN ĐỀ!")
else:
    print("✅ TÌM THẤY MỰC - OK!")
