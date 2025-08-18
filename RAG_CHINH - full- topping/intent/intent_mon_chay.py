import re

def handle_intent_mon_chay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món chay nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(món chay|mon chay|chay).*không", norm_input):
        mon_chay_da_tra = set()
        for turn in history:
            if 'mon_chay_suggested' in turn:
                mon_chay_da_tra.update(turn['mon_chay_suggested'])
        candidates = search_pinecone("món chay", top_k=200)
        mon_chay = []
        for doc in candidates:
            if doc.get('chay_man', '').lower() == 'chay':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_chay_da_tra:
                    mon_chay.append(doc)
        if not mon_chay:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chay trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chay_suggested = []
        else:
            answer_lines = ["Dưới đây là các món chay còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_chay_suggested = []
            for doc in mon_chay[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chay_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chay_suggested
    # Nhận diện các câu hỏi về món chay nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|món chay|mon chay|chay)", norm_input) and ("chay" in norm_input):
        mon_chay_da_tra = set()
        for turn in history:
            if 'mon_chay_suggested' in turn:
                mon_chay_da_tra.update(turn['mon_chay_suggested'])
        candidates = search_pinecone("món chay", top_k=200)
        mon_chay = []
        for doc in candidates:
            if doc.get('chay_man', '').lower() == 'chay':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_chay_da_tra:
                    mon_chay.append(doc)
        if not mon_chay:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chay trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chay_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món chay bạn có thể tham khảo:"]
            mon_chay_suggested = []
            for doc in mon_chay[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chay_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chay_suggested
    return None, None
