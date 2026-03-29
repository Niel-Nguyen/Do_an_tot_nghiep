import re

# Test regex patterns
test_inputs = [
    "Tôi muốn món nấu nhanh dưới 20 phút",
    "Cho tôi 3 món chay ngon",
    "Gợi ý cho tôi 5 món ăn ngon",
    "Có lẩu tôm chua không"
]

question_patterns = [
    r'có\s+.+\s+(không|ko)\b',
    r'nhà\s+hàng\s+có\s+.+\s+(không|ko)\b',
    r'.+\s+(có|còn)\s+(không|ko)\b',
    r'menu\s+có\s+.+\s+(không|ko)\b',
    r'.+\s+là\s+(món\s+)?gì\b',
    r'(cho\s+tôi\s+biết|giới\s+thiệu|thông\s+tin\s+về|tìm\s+hiểu).+',
    r'.+\s+(như\s+thế\s+nào|ra\s+sao|thế\s+nào)\b',
    r'(bao\s+nhiêu|giá\s+cả|giá\s+tiền|bán\s+giá).+',
    r'(cho\s+tôi|gợi\s+ý|tư\s+vấn).+(món\s+gì|món\s+nào|thức\s+ăn|đồ\s+ăn)',
    r'.+(miền\s+\w+|vùng\s+\w+).+(dưới|trên|khoảng|tầm|giá).+',
    r'.+(dưới|trên|khoảng|tầm)\s+\d+.+(ngàn|nghìn|đồng|k)',
    r'(cho\s+tôi|gợi\s+ý)\s+\d+\s+(món|thức\s+ăn).+(ngon|tốt|hay|nổi\s+tiếng)',
    r'.+(món|thức\s+ăn).+(nấu\s+nhanh|làm\s+nhanh|chế\s+biến\s+nhanh)',
    r'.+(dưới|trên|khoảng|tầm)\s+\d+\s+(phút|giờ).+(nấu|làm|chế\s+biến)',
    r'(muốn|cần)\s+(món|thức\s+ăn).+(nhanh|dưới|tầm)\s+\d+\s+(phút|giờ)',
]

for test_input in test_inputs:
    print(f'\n=== Test input: "{test_input}" ===')
    
    is_question = False
    matched_patterns = []
    
    for i, pattern in enumerate(question_patterns):
        match = re.search(pattern, test_input.lower())
        if match:
            print(f'Pattern {i+1}: ✅ MATCH - {pattern}')
            matched_patterns.append(i+1)
            is_question = True
    
    if not matched_patterns:
        print('❌ No patterns matched')
    
    print(f'Result: {"QUESTION" if is_question else "ORDER"} (Patterns: {matched_patterns})')
