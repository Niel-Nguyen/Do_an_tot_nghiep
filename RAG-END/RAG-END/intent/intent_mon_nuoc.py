import re

def handle_intent_mon_nuoc(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món nước nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(món nước|mon nuoc|nước|nuoc).*không", norm_input):
        mon_nuoc_da_tra = set()
        for turn in history:
            if 'mon_nuoc_suggested' in turn:
                mon_nuoc_da_tra.update(turn['mon_nuoc_suggested'])
        candidates = search_pinecone("món nước", top_k=200)
        mon_nuoc = []
        for doc in candidates:
            kho_nuoc = doc.get('kho_nuoc', '').lower()
            if kho_nuoc == 'nước' or kho_nuoc == 'nuoc' or 'nước' in kho_nuoc or 'nuoc' in kho_nuoc:
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_nuoc_da_tra:
                    mon_nuoc.append(doc)
        if not mon_nuoc:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món nước trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_nuoc_suggested = []
        else:
            answer_lines = ["Dưới đây là các món nước còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_nuoc_suggested = []
            for doc in mon_nuoc[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_nuoc_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_nuoc_suggested
    # Nhận diện các câu hỏi về món nước nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|món nước|mon nuoc|nước|nuoc)", norm_input) and ("nuoc" in norm_input or "nước" in norm_input):
        mon_nuoc_da_tra = set()
        for turn in history:
            if 'mon_nuoc_suggested' in turn:
                mon_nuoc_da_tra.update(turn['mon_nuoc_suggested'])
        candidates = search_pinecone("món nước", top_k=200)
        mon_nuoc = []
        for doc in candidates:
            kho_nuoc = doc.get('kho_nuoc', '').lower()
            if kho_nuoc == 'nước' or kho_nuoc == 'nuoc' or 'nước' in kho_nuoc or 'nuoc' in kho_nuoc:
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_nuoc_da_tra:
                    mon_nuoc.append(doc)
        if not mon_nuoc:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món nước trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_nuoc_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món nước bạn có thể tham khảo:"]
            mon_nuoc_suggested = []
            for doc in mon_nuoc[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_nuoc_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_nuoc_suggested
    return None, None
