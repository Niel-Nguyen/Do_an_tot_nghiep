import re

def handle_intent_com(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    # Regex loại trừ mở rộng nhận diện mọi biến thể hỏi về cách làm/nấu
    if re.search(r"cách[\s_]*(làm|nấu|che bien|chế biến)|cong thuc|công thức|làm[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|nấu[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|hướng dẫn|làm món|nấu món|chế biến món|cach lam|cach nau|cach che bien|cach che bien mon|cach nau mon|cach lam mon|cach che bien|cach che bien mon|cach che bien|cach che bien mon", user_input.lower()):
        return None, None
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn cơm nào khác không" hoặc tương tự (chỉ khi KHÔNG có từ khóa về cách làm/nấu)
    if re.search(r"(còn|con|thêm|them).*(cơm|com).*không", norm_input):
        mon_com_da_tra = set()
        for turn in history:
            if 'mon_com_suggested' in turn:
                mon_com_da_tra.update(turn['mon_com_suggested'])
        candidates = search_pinecone("cơm", top_k=300)
        mon_com = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("com" in ten_mon_norm or "cơm" in ten_mon_norm) and ten_mon not in mon_com_da_tra:
                mon_com.append(doc)
        if not mon_com:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cơm trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_com_suggested = []
        else:
            answer_lines = ["Dưới đây là các món cơm còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_com_suggested = []
            for doc in mon_com[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_com_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_com_suggested
    # Nhận diện các câu hỏi về cơm nói chung (chỉ khi KHÔNG có từ khóa về cách làm/nấu)
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|cơm|com)", norm_input) and ("com" in norm_input or "cơm" in norm_input):
        mon_com_da_tra = set()
        for turn in history:
            if 'mon_com_suggested' in turn:
                mon_com_da_tra.update(turn['mon_com_suggested'])
        candidates = search_pinecone("cơm", top_k=200)
        mon_com = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("com" in ten_mon_norm or "cơm" in ten_mon_norm) and ten_mon not in mon_com_da_tra:
                mon_com.append(doc)
        if not mon_com:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cơm trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_com_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món cơm bạn có thể tham khảo:"]
            mon_com_suggested = []
            for doc in mon_com[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_com_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_com_suggested
    return None, None
