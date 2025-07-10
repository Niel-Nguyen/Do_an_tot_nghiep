import re

def handle_intent_mon_bun(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn bún nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(bún|bun).*không", norm_input):
        mon_bun_da_tra = set()
        for turn in history:
            if 'mon_bun_suggested' in turn:
                mon_bun_da_tra.update(turn['mon_bun_suggested'])
        candidates = search_pinecone("bún", top_k=200)
        mon_bun = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("bun" in ten_mon_norm or "bún" in ten_mon_norm) and ten_mon not in mon_bun_da_tra:
                mon_bun.append(doc)
        if not mon_bun:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món bún trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_bun_suggested = []
        else:
            answer_lines = ["Dưới đây là các món bún còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_bun_suggested = []
            for doc in mon_bun[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_bun_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_bun_suggested
    # Nhận diện các câu hỏi về bún nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|bún|bun)", norm_input) and ("bun" in norm_input or "bún" in norm_input):
        mon_bun_da_tra = set()
        for turn in history:
            if 'mon_bun_suggested' in turn:
                mon_bun_da_tra.update(turn['mon_bun_suggested'])
        candidates = search_pinecone("bún", top_k=200)
        mon_bun = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            ten_mon_norm = normalize_text(ten_mon)
            if ("bun" in ten_mon_norm or "bún" in ten_mon_norm) and ten_mon not in mon_bun_da_tra:
                mon_bun.append(doc)
        if not mon_bun:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món bún trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_bun_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món bún bạn có thể tham khảo:"]
            mon_bun_suggested = []
            for doc in mon_bun[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_bun_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_bun_suggested
    return None, None
