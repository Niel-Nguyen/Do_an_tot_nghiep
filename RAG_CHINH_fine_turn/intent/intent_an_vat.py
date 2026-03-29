import re

def handle_intent_an_vat(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món ăn vặt nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(ăn vặt|an vat|vặt|vat).*không", norm_input):
        mon_vat_da_tra = set()
        for turn in history:
            if 'mon_vat_suggested' in turn:
                mon_vat_da_tra.update(turn['mon_vat_suggested'])
        candidates = search_pinecone("ăn vặt", top_k=200)
        mon_vat = []
        for doc in candidates:
            if doc.get('chinh_vat', '').lower() == 'vặt' or doc.get('chinh_vat', '').lower() == 'vat':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_vat_da_tra:
                    mon_vat.append(doc)
        if not mon_vat:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món ăn vặt trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_vat_suggested = []
        else:
            answer_lines = ["Dưới đây là các món ăn vặt còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_vat_suggested = []
            for doc in mon_vat[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_vat_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_vat_suggested
    # Nhận diện các câu hỏi về món ăn vặt nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|ăn vặt|an vat|vặt|vat)", norm_input) and ("vat" in norm_input or "vặt" in norm_input):
        mon_vat_da_tra = set()
        for turn in history:
            if 'mon_vat_suggested' in turn:
                mon_vat_da_tra.update(turn['mon_vat_suggested'])
        candidates = search_pinecone("ăn vặt", top_k=200)
        mon_vat = []
        for doc in candidates:
            if doc.get('chinh_vat', '').lower() == 'vặt' or doc.get('chinh_vat', '').lower() == 'vat':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_vat_da_tra:
                    mon_vat.append(doc)
        if not mon_vat:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món ăn vặt trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_vat_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món ăn vặt bạn có thể tham khảo:"]
            mon_vat_suggested = []
            for doc in mon_vat[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_vat_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_vat_suggested
    return None, None
