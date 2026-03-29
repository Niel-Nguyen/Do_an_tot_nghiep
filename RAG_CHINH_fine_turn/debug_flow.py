import re

# Test để debug flow xử lý
test_input = "cho tôi 3 món chay ngon"

# Question patterns
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
]

# Order phrases  
order_phrases = [
    "gọi", "order", "đặt", "cho tôi", "cho mình", "cho em", "thêm", "thêm món", "lấy", "muốn ăn", "ăn", "mua", "add",
    "muốn order món", "tôi muốn gọi món", "mình muốn", "em muốn", "tôi gọi", "mình gọi", "em gọi",
    "lấy cho", "đưa cho", "phục vụ", "mang", "có thể cho", "xin", "dùng", "ăn thử",
    "phần", "suất", "dĩa", "bát", "ly", "cốc", "miếng", "cái", "tô", "chén"
]

# Info phrases
info_phrases = [
    "tìm hiểu món", "giới thiệu món", "món", "thông tin món", "món này là gì", "món này có gì đặc biệt", 
    "món này ngon không", "món này có gì", "món ... là gì", "món ... có gì đặc biệt"
]

print(f"Testing: '{test_input}'")
print()

# Check is_question
is_question = any(re.search(pattern, test_input.lower()) for pattern in question_patterns)
print(f"is_question: {is_question}")

# Check order phrases
has_order_phrase = any(phrase in test_input.lower() for phrase in order_phrases)
print(f"has_order_phrase: {has_order_phrase}")

# Check info phrases  
has_info_phrase = any(phrase in test_input.lower() for phrase in info_phrases)
print(f"has_info_phrase: {has_info_phrase}")

print()
print("Logic flow:")
print(f"1. is_question = {is_question}")
print(f"2. not is_question and has_order_phrase = {not is_question and has_order_phrase}")
print(f"3. has_info_phrase = {has_info_phrase}")
print(f"4. not is_question and not(has_order_phrase or has_info_phrase) = {not is_question and not (has_order_phrase or has_info_phrase)}")

print()
print("Expected flow:")
if is_question:
    print("-> Should go to LLM for question answering")
elif not is_question and has_order_phrase:
    print("-> Should process as order")
elif has_info_phrase:
    print("-> Should show dish info")
elif not is_question and not (has_order_phrase or has_info_phrase):
    print("-> Should show dish info (auto-detect)")
else:
    print("-> Should go to LLM")
