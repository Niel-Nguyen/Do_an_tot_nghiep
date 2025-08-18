import re

def handle_intent_mon_kho(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món kho nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(món kho|mon kho|kho|khô|khô|kho).*không", norm_input):
        mon_kho_da_tra = set()
        for turn in history:
            if 'mon_kho_suggested' in turn:
                mon_kho_da_tra.update(turn['mon_kho_suggested'])
        candidates = search_pinecone("món kho", top_k=200)
        mon_kho = []
        for doc in candidates:
            kho_nuoc = doc.get('kho_nuoc', '').lower()
            if kho_nuoc == 'khô' or kho_nuoc == 'kho' or 'khô' in kho_nuoc or 'kho' in kho_nuoc:
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_kho_da_tra:
                    mon_kho.append(doc)
        if not mon_kho:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món khô trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_kho_suggested = []
        else:
            answer_lines = ["Dưới đây là các món khô còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_kho_suggested = []
            for doc in mon_kho[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_kho_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_kho_suggested
    # Nhận diện các câu hỏi về món kho nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|món kho|mon kho|kho|khô)", norm_input) and ("kho" in norm_input or "khô" in norm_input):
        mon_kho_da_tra = set()
        for turn in history:
            if 'mon_kho_suggested' in turn:
                mon_kho_da_tra.update(turn['mon_kho_suggested'])
        candidates = search_pinecone("món kho", top_k=200)
        mon_kho = []
        for doc in candidates:
            kho_nuoc = doc.get('kho_nuoc', '').lower()
            if kho_nuoc == 'khô' or kho_nuoc == 'kho' or 'khô' in kho_nuoc or 'kho' in kho_nuoc:
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_kho_da_tra:
                    mon_kho.append(doc)
        if not mon_kho:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món kho trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_kho_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món kho bạn có thể tham khảo:"]
            mon_kho_suggested = []
            for doc in mon_kho[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_kho_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_kho_suggested
    return None, None
