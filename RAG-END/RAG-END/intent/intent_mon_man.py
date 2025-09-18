import re

def handle_intent_mon_man(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món mặn nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(món mặn|mon man|mặn|man).*không", norm_input):
        mon_man_da_tra = set()
        for turn in history:
            if 'mon_man_suggested' in turn:
                mon_man_da_tra.update(turn['mon_man_suggested'])
        candidates = search_pinecone("món mặn", top_k=200)
        mon_man = []
        for doc in candidates:
            if doc.get('chay_man', '').lower() == 'mặn' or doc.get('chay_man', '').lower() == 'man':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_man_da_tra:
                    mon_man.append(doc)
        if not mon_man:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món mặn trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_man_suggested = []
        else:
            answer_lines = ["Dưới đây là các món mặn còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_man_suggested = []
            for doc in mon_man[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_man_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_man_suggested
    # Nhận diện các câu hỏi về món mặn nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|món mặn|mon man|mặn|man)", norm_input) and ("man" in norm_input or "mặn" in norm_input):
        mon_man_da_tra = set()
        for turn in history:
            if 'mon_man_suggested' in turn:
                mon_man_da_tra.update(turn['mon_man_suggested'])
        candidates = search_pinecone("món mặn", top_k=200)
        mon_man = []
        for doc in candidates:
            if doc.get('chay_man', '').lower() == 'mặn' or doc.get('chay_man', '').lower() == 'man':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_man_da_tra:
                    mon_man.append(doc)
        if not mon_man:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món mặn trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_man_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món mặn bạn có thể tham khảo:"]
            mon_man_suggested = []
            for doc in mon_man[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_man_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_man_suggested
    return None, None
