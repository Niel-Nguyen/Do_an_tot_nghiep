import re

def handle_intent_an_chinh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    norm_input = normalize_text(user_input)
    # Nhận diện câu hỏi "còn món chính nào khác không" hoặc tương tự
    if re.search(r"(còn|con|thêm|them).*(món chính|mon chinh|chính|chinh).*không", norm_input):
        mon_chinh_da_tra = set()
        for turn in history:
            if 'mon_chinh_suggested' in turn:
                mon_chinh_da_tra.update(turn['mon_chinh_suggested'])
        candidates = search_pinecone("món chính", top_k=200)
        mon_chinh = []
        for doc in candidates:
            if doc.get('chinh_vat', '').lower() == 'chính' or doc.get('chinh_vat', '').lower() == 'chinh':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_chinh_da_tra:
                    mon_chinh.append(doc)
        if not mon_chinh:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chính trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chinh_suggested = []
        else:
            answer_lines = ["Dưới đây là các món chính còn lại trong nhà hàng mà bạn chưa xem:"]
            mon_chinh_suggested = []
            for doc in mon_chinh[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chinh_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chinh_suggested
    # Nhận diện các câu hỏi về món chính nói chung
    if re.search(r"(gợi ý|goi y|nào ngon|gi hợp|món chính|mon chinh|chính|chinh)", norm_input) and ("chinh" in norm_input or "chính" in norm_input):
        mon_chinh_da_tra = set()
        for turn in history:
            if 'mon_chinh_suggested' in turn:
                mon_chinh_da_tra.update(turn['mon_chinh_suggested'])
        candidates = search_pinecone("món chính", top_k=200)
        mon_chinh = []
        for doc in candidates:
            if doc.get('chinh_vat', '').lower() == 'chính' or doc.get('chinh_vat', '').lower() == 'chinh':
                ten_mon = doc.get('mon_an', '')
                if ten_mon not in mon_chinh_da_tra:
                    mon_chinh.append(doc)
        if not mon_chinh:
            answer = "Hiện tại mình đã giới thiệu hết tất cả các món chính trong nhà hàng rồi ạ. Khách iu có muốn tham khảo món khác không?"
            mon_chinh_suggested = []
        else:
            answer_lines = ["Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là một số món chính bạn có thể tham khảo:"]
            mon_chinh_suggested = []
            for doc in mon_chinh[:7]:
                ten_mon = doc.get('mon_an', '')
                vung_mien = doc.get('vung_mien', '')
                mo_ta = doc.get('mo_ta', '')
                answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien}): {mo_ta}")
                mon_chinh_suggested.append(ten_mon)
            answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
        return answer, mon_chinh_suggested
    return None, None
