import re

def handle_intent_nguyen_lieu(user_input, history, find_best_match, get_bot_response):
    match_nguyenlieu = re.match(r"nguyên liệu (làm )?(.+)", user_input.lower())
    if match_nguyenlieu:
        ten_mon_query = match_nguyenlieu.group(2).strip()
        found, candidates = find_best_match(ten_mon_query)
        if found:
            nguyen_lieu = found.get('nguyen_lieu') or found.get('nguyên liệu')
            if nguyen_lieu:
                prompt = (
                    "Bạn là MC ảo của nhà hàng XYZ. Hãy trả lời thân thiện, dẫn dắt, gợi mở, nhưng chỉ sử dụng đúng nội dung sau để trả lời khách, không tự bịa thêm nguyên liệu.\n"
                    f"Tên món: {found.get('mon_an','')}\n"
                    f"Nguyên liệu: {nguyen_lieu}\n"
                    f"Lịch sử hội thoại: {history[-3:]}\n"
                    f"Khách hỏi: {user_input}\n"
                    "MC trả lời:"
                )
            else:
                prompt = (
                    "Bạn là MC ảo của nhà hàng XYZ. Khách hỏi về nguyên liệu một món ăn nhưng không có dữ liệu. Hãy xin lỗi nhẹ nhàng và gợi ý khách hỏi món khác.\n"
                    f"Tên món: {found.get('mon_an','')}\n"
                    f"Lịch sử hội thoại: {history[-3:]}\n"
                    f"Khách hỏi: {user_input}\n"
                    "MC trả lời:"
                )
            answer = get_bot_response(prompt)
            return answer
    return None
