import re

def handle_intent_che(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    # Regex loại trừ mở rộng nhận diện mọi biến thể hỏi về cách làm/nấu
    if re.search(r"cách[\s_]*(làm|nấu|che bien|chế biến)|cong thuc|công thức|làm[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|nấu[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|hướng dẫn|làm món|nấu món|chế biến món|cach lam|cach nau|cach che bien|cach che bien mon|cach nau mon|cach lam mon|cach che bien|cach che bien mon|cach che bien|cach che bien mon", user_input.lower()):
        return None, None
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn chè nào khác không" hoặc tương tự (chỉ khi KHÔNG có từ khóa về cách làm/nấu)
    if re.search(r"(còn|con|thêm|them).*(\bchè\b|\bche\b).*không", norm_input):
        mon_che_da_tra = set()
        for turn in history:
            if 'mon_che_suggested' in turn:
                mon_che_da_tra.update(turn['mon_che_suggested'])
        candidates = search_pinecone("chè", top_k=200)
        mon_che = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("che" in ten_mon_norm or "chè" in ten_mon_norm) and ten_mon not in mon_che_da_tra:
                mon_che.append(doc)
        if not mon_che:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chè trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_che_suggested = []
        else:
            answer_lines = ["Dưới đây là các món chè còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_che_suggested = []
            for doc in mon_che[:10]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_che_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_che_suggested
    # Nhận diện các câu hỏi về chè nói chung (chỉ khi KHÔNG có từ khóa về cách làm/nấu)
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|\bchè\b|\bche\b)", norm_input) and ("che" in norm_input or "chè" in norm_input):
        mon_che_da_tra = set()
        for turn in history:
            if 'mon_che_suggested' in turn:
                mon_che_da_tra.update(turn['mon_che_suggested'])
        candidates = search_pinecone("chè", top_k=200)
        mon_che = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("che" in ten_mon_norm or "chè" in ten_mon_norm) and ten_mon not in mon_che_da_tra:
                mon_che.append(doc)
        if not mon_che:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chè trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_che_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món chè bạn có thể tham khảo:"]
            mon_che_suggested = []
            for doc in mon_che[:10]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_che_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_che_suggested
    return None, None
