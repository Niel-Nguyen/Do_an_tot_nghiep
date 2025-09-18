import re

def handle_intent_chao(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    # Nhận diện mọi biến thể hỏi về cháo, kể cả "gợi ý món cháo", "cháo nào ngon", "cháo gì hợp sáng", ...
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn cháo nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(cháo|chao).*không", norm_input):
        mon_chao_da_tra = set()
        for turn in history:
            if 'mon_chao_suggested' in turn:
                mon_chao_da_tra.update(turn['mon_chao_suggested'])
        candidates = search_pinecone("cháo", top_k=200)
        mon_chao = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("chao" in ten_mon_norm or "cháo" in ten_mon_norm) and ten_mon not in mon_chao_da_tra:
                mon_chao.append(doc)
        if not mon_chao:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cháo trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chao_suggested = []
        else:
            answer_lines = ["Dưới đây là các món cháo còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_chao_suggested = []
            for doc in mon_chao[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chao_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chao_suggested
    # Nhận diện các câu hỏi về cháo nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|cháo|chao)", norm_input) and ("chao" in norm_input or "cháo" in norm_input):
        mon_chao_da_tra = set()
        for turn in history:
            if 'mon_chao_suggested' in turn:
                mon_chao_da_tra.update(turn['mon_chao_suggested'])
        candidates = search_pinecone("cháo", top_k=200)
        mon_chao = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("chao" in ten_mon_norm or "cháo" in ten_mon_norm) and ten_mon not in mon_chao_da_tra:
                mon_chao.append(doc)
        if not mon_chao:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cháo trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chao_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món cháo bạn có thể tham khảo:"]
            mon_chao_suggested = []
            for doc in mon_chao[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chao_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chao_suggested
    return None, None
