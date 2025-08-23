import re

# Test regex patterns
test_input = "Cho tôi 3 món chay ngon"

question_patterns = [
    r'có\s+.+\s+(không|ko)\b',  # "có ... không"
    r'nhà\s+hàng\s+có\s+.+\s+(không|ko)\b',  # "nhà hàng có ... không"
    r'.+\s+(có|còn)\s+(không|ko)\b',  # "... có không", "... còn không"
    r'menu\s+có\s+.+\s+(không|ko)\b',  # "menu có ... không"
    r'.+\s+là\s+(món\s+)?gì\b',  # "... là món gì", "... là gì"
    r'(cho\s+tôi\s+biết|giới\s+thiệu|thông\s+tin\s+về|tìm\s+hiểu).+',  # câu hỏi thông tin
    r'.+\s+(như\s+thế\s+nào|ra\s+sao|thế\s+nào)\b',  # "... như thế nào"
    r'(bao\s+nhiêu|giá\s+cả|giá\s+tiền|bán\s+giá).+',  # câu hỏi về giá
    r'(cho\s+tôi|gợi\s+ý|tư\s+vấn).+(món\s+gì|món\s+nào|thức\s+ăn|đồ\s+ăn)',  # câu hỏi gợi ý
    r'.+(miền\s+\w+|vùng\s+\w+).+(dưới|trên|khoảng|tầm|giá).+',  # câu hỏi theo vùng miền + giá
    r'.+(dưới|trên|khoảng|tầm)\s+\d+.+(ngàn|nghìn|đồng|k)',  # câu hỏi về mức giá
]

print(f'Test input: {test_input}')
print('Checking question patterns:')

is_question = False
for i, pattern in enumerate(question_patterns):
    match = re.search(pattern, test_input.lower())
    if match:
        print(f'Pattern {i+1}: ✅ MATCH - {pattern}')
        is_question = True
    else:
        print(f'Pattern {i+1}: ❌ No match - {pattern}')

print(f'\nIs question? {is_question}')
