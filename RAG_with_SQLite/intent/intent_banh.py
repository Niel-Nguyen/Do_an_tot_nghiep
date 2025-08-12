import re

def handle_intent_banh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn bánh nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(bánh|banh).*không", norm_input):
        mon_banh_da_tra = set()
        for turn in history:
            if 'mon_banh_suggested' in turn:
                mon_banh_da_tra.update(turn['mon_banh_suggested'])
        candidates = search_pinecone("bánh", top_k=200)
        mon_banh = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("banh" in ten_mon_norm or "bánh" in ten_mon_norm) and ten_mon not in mon_banh_da_tra:
                mon_banh.append(doc)
        if not mon_banh:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món bánh trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_banh_suggested = []
        else:
            answer_lines = ["Dưới đây là các món bánh còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_banh_suggested = []
            for doc in mon_banh[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_banh_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_banh_suggested
    # Nhận diện các câu hỏi về bánh nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|bánh|banh)", norm_input) and ("banh" in norm_input or "bánh" in norm_input):
        mon_banh_da_tra = set()
        for turn in history:
            if 'mon_banh_suggested' in turn:
                mon_banh_da_tra.update(turn['mon_banh_suggested'])
        candidates = search_pinecone("bánh", top_k=200)
        mon_banh = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("banh" in ten_mon_norm or "bánh" in ten_mon_norm) and ten_mon not in mon_banh_da_tra:
                mon_banh.append(doc)
        if not mon_banh:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món bánh trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_banh_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món bánh khách iu có thể tham khảo ạ:"]
            mon_banh_suggested = []
            for doc in mon_banh[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_banh_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_banh_suggested
    return None, None
