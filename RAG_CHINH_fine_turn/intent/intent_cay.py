import re

def handle_intent_cay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món cay nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(cay|ớt|spicy).*không", norm_input):
        mon_cay_da_tra = set()
        for turn in history:
            if 'mon_cay_suggested' in turn:
                mon_cay_da_tra.update(turn['mon_cay_suggested'])
        candidates = search_pinecone("cay", top_k=200)
        mon_cay = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            nguyen_lieu = (doc.get('nguyen_lieu', '') + ' ' + doc.get('nguyên liệu', '')).lower()
            mo_ta = doc.get('mo_ta', '').lower()
            if ("cay" in mo_ta or "ớt" in nguyen_lieu or "ớt" in mo_ta or "spicy" in mo_ta) and ten_mon not in mon_cay_da_tra:
                mon_cay.append(doc)
        if not mon_cay:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cay trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_cay_suggested = []
        else:
            answer_lines = ["Dưới đây là các món cay còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_cay_suggested = []
            for doc in mon_cay[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_cay_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_cay_suggested
    # Nhận diện các câu hỏi về món cay nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|cay|ớt|spicy)", norm_input) and ("cay" in norm_input or "ớt" in norm_input or "spicy" in norm_input):
        mon_cay_da_tra = set()
        for turn in history:
            if 'mon_cay_suggested' in turn:
                mon_cay_da_tra.update(turn['mon_cay_suggested'])
        candidates = search_pinecone("cay", top_k=200)
        mon_cay = []
        for doc in candidates:
            ten_mon = doc.get('mon_an', '')
            nguyen_lieu = (doc.get('nguyen_lieu', '') + ' ' + doc.get('nguyên liệu', '')).lower()
            mo_ta = doc.get('mo_ta', '').lower()
            if ("cay" in mo_ta or "ớt" in nguyen_lieu or "ớt" in mo_ta or "spicy" in mo_ta) and ten_mon not in mon_cay_da_tra:
                mon_cay.append(doc)
        if not mon_cay:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món cay trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_cay_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món cay bạn có thể tham khảo:"]
            mon_cay_suggested = []
            for doc in mon_cay[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_cay_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_cay_suggested
    return None, None
