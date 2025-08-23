#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Test question patterns
user_message = "có món nào có gà không"
print(f"Testing message: '{user_message}'")

question_patterns = [
    r'có\s+(.+?)\s+(không|ko)\s*\?*$',
    r'(.+?)\s+có\s+(không|ko)\s*\?*$',
    r'nhà\s+hàng\s+có\s+(.+?)\s+(không|ko)\s*\?*$'
]

for i, pattern in enumerate(question_patterns):
    print(f"\nPattern {i+1}: {pattern}")
    match = re.search(pattern, user_message.lower().strip())
    if match:
        potential_dish = match.group(1).strip()
        print(f"✅ MATCH! potential_dish: '{potential_dish}'")
        break
    else:
        print("❌ NO MATCH")
else:
    print("\n❌ NO PATTERN MATCHED")
