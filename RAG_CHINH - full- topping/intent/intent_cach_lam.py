import re

def clean_ten_mon(ten_mon):
    # Loại bỏ các từ phụ, action cuối câu nếu bị dính vào tên món
    action_suffixes = [
        'làm thế nào', 'làm như nào', 'làm như thế nào', 'nấu thế nào', 'nấu như nào', 'nấu như thế nào',
        'che bien nhu the nao', 'chế biến như thế nào', 'chế biến như nào', 'nấu ra sao', 'làm ra sao',
        'nau nhu the nao', 'nau nhu nao', 'chế biến', 'làm', 'nấu', 'ra sao', 'thế nào', 'như nào', 'như thế nào'
    ]
    ten_mon = ten_mon.strip(' .?!,;:')
    for suffix in action_suffixes:
        if ten_mon.lower().endswith(suffix):
            ten_mon = ten_mon[: -len(suffix)].strip(' .?!,;:')
    return ten_mon

def handle_intent_cach_lam(user_input, history, find_best_match, get_bot_response):
    norm_input = user_input.lower()
    # Các cụm từ hỏi về cách làm
    ending_phrases = [
        "làm thế nào", "làm như nào", "làm như thế nào", "nấu thế nào", "nấu như nào", "nấu như thế nào",
        "che bien nhu the nao", "chế biến như thế nào", "chế biến như nào", "nấu ra sao", "làm ra sao",
        "nau nhu the nao", "nau nhu nao", "thế nào", "như nào", "như thế nào", "ra sao"
    ]
    # Các pattern ưu tiên tách tên món chính xác
    patterns = [
        # "món <tên món> <cụm hỏi>"
        r"m[oó]n ([^\n]+?) (làm thế nào|làm như nào|làm như thế nào|nấu thế nào|nấu như nào|nấu như thế nào|che bien nhu the nao|chế biến như thế nào|chế biến như nào|nấu ra sao|làm ra sao|nau nhu the nao|nau nhu nao)",
        # "<tên món> <cụm hỏi>" (không cần từ 'món', ưu tiên non-greedy)
        r"([^\n]+?) (làm thế nào|làm như nào|làm như thế nào|nấu thế nào|nấu như nào|nấu như thế nào|che bien nhu the nao|chế biến như thế nào|chế biến như nào|nấu ra sao|làm ra sao|nau nhu the nao|nau nhu nao)$",
        # "cách làm ...", "cách nấu ...", ...
        r"(cách làm|cach lam|cách nấu|cach nau|cách chế biến|cach che bien|công thức|cong thuc|làm món|nấu món|che bien mon|chế biến món|cach lam mon|cach nau mon|cach che bien mon|làm sao để|hướng dẫn làm|hướng dẫn nấu|huong dan lam|huong dan nau|làm như thế nào|lam nhu the nao|nấu ra sao|nau ra sao|làm ra sao|lam ra sao) ([^\n]+)",
        # "làm/nấu/chế biến <tên món> như thế nào/ra sao/..."
        r"(làm|nấu|che bien|chế biến) ([^\n]+) như thế nào",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) ra sao",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) kiểu gì",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) kiểu nào",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) được không",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) sao cho ngon",
        r"(làm|nấu|che bien|chế biến) ([^\n]+) ngon nhất",
        r"(cach lam|cach nau|cach che bien) ([^\n]+)",
        # "<tên món> chế biến/làm/nấu thế nào/ra sao/..."
        r"([a-zA-ZÀ-ỹ0-9\s]+) (chế biến|làm|nấu) (thế nào|như nào|như thế nào|ra sao)",
    ]
    match_cachlam = None
    ten_mon_query = None
    for pat in patterns:
        m = re.search(pat, norm_input)
        if m:
            # Xác định group nào là tên món
            if pat == patterns[0]:  # "m[oó]n ([^\n]+?) (làm như nào|...)"
                ten_mon_query = m.group(1).strip()
            elif pat == patterns[1]:  # ".+ (làm như nào|...)"
                ten_mon_query = m.group(1).strip()
            elif len(m.groups()) >= 2 and m.group(2):
                if m.group(2).strip() in ["chế biến", "làm", "nấu"] and m.group(1):
                    ten_mon_query = m.group(1).strip()
                else:
                    ten_mon_query = m.group(2).strip()
            else:
                for i in range(len(m.groups()), 0, -1):
                    if m.group(i):
                        ten_mon_query = m.group(i).strip()
                        break
            match_cachlam = m
            break
    if match_cachlam and ten_mon_query:
        ten_mon_query_clean = clean_ten_mon(ten_mon_query)
        found, candidates = find_best_match(ten_mon_query_clean)
        # Nếu không tìm thấy, thử lại với tên món gốc (phòng trường hợp clean bị cắt quá nhiều)
        if not found and ten_mon_query_clean != ten_mon_query:
            found, candidates = find_best_match(ten_mon_query)
        if found:
            cach_lam = found.get('cach_lam') or found.get('cách làm/công thức')
            if cach_lam:
                prompt = (
                    "Bạn là MC ảo của nhà hàng Phúc Đẹp Chai. Hãy trả lời thân thiện, dẫn dắt, gợi mở, nhưng chỉ sử dụng đúng nội dung sau để trả lời khách, không tự bịa thêm công thức.\n"
                    f"Tên món: {found.get('mon_an','')}\n"
                    f"Cách làm: {cach_lam}\n"
                    f"Lịch sử hội thoại: {history[-3:]}\n"
                    f"Khách hỏi: {user_input}\n"
                    "MC trả lời:"
                )
            else:
                prompt = (
                    "Bạn là MC ảo của nhà hàng Phúc Đẹp Chai. Khách hỏi về cách làm một món ăn nhưng không có dữ liệu. Hãy xin lỗi nhẹ nhàng và gợi ý khách hỏi món khác.\n"
                    f"Tên món: {found.get('mon_an','')}\n"
                    f"Lịch sử hội thoại: {history[-3:]}\n"
                    f"Khách hỏi: {user_input}\n"
                    "MC trả lời:"
                )
            answer = get_bot_response(prompt)
            return answer
    return None
