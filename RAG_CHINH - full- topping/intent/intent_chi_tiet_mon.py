import re
import random

def handle_intent_chi_tiet_mon(user_input, history, find_best_match):
    """
    Nếu user vừa xác nhận muốn biết thêm về món ("có", "tôi muốn biết", ...), lấy món gần nhất bot vừa xác nhận có, trả về chi tiết món (tên, vùng miền, mô tả, hình ảnh) và gợi ý tiếp.
    Chỉ trả về chi tiết nếu user_input là xác nhận (không phải câu hỏi về sự tồn tại món ăn mới).
    """
    # Nhận diện xác nhận muốn biết thêm (mở rộng pattern)
    confirm_patterns = [
        r"^(có|muốn biết|tôi muốn biết|xem chi tiết|chi tiết|thông tin|xem thêm|cho xem|xem món|xem thông tin|ok|yes|được|dạ|vâng|ừ|uh|uhm|ờ|ừm|cho hỏi|hỏi thêm|thêm chi tiết|thêm thông tin|thêm|more|detail|details|info|information)($|\s)",
        r"^(tôi muốn|em muốn|mình muốn|anh muốn|chị muốn|muốn|cho mình biết|cho em biết|cho anh biết|cho chị biết|cho tôi biết|cho biết|muốn xem|muốn hỏi|muốn tìm hiểu|giới thiệu|show|show me|tell me|tell us|can you show|can you tell|can i see|can i know|can you give|can you provide|can you share)($|\s|\W)",
        r"^(yes|yeah|yep|y|sure|please|please do|please show|please tell|please give|please provide|please share)($|\s|\W)",
        r"^(mở rộng|chi tiết hơn|thêm thông tin|thêm mô tả|thêm hình ảnh|thêm ảnh|thêm|more|details|info|information)($|\s|\W)"
    ]
    # Nếu user hỏi về sự tồn tại món ăn (có ... không), KHÔNG coi là xác nhận chi tiết
    if re.search(r"có\s+.+\s+không", user_input.lower()):
        return None
    if not any(re.match(pat, user_input.strip(), re.IGNORECASE) for pat in confirm_patterns):
        return None
    # Tìm món gần nhất bot vừa xác nhận có
    for msg in reversed(history):
        if msg.get('bot') and 'có món' in msg['bot']:
            m = re.search(r"có món ([^\n]+?) nhé", msg['bot'], re.IGNORECASE)
            if m:
                ten_mon = m.group(1).strip()
                found, _ = find_best_match(ten_mon)
                if found:
                    ten_mon = found.get('mon_an', ten_mon)
                    vung_mien = found.get('vung_mien', 'Không rõ')
                    mo_ta = found.get('mo_ta', 'Chưa có mô tả.')
                    img_url = found.get('hinh_anh')
                    html = f"<b>{ten_mon}</b>"
                    html += f"<br><b>Vùng miền:</b> {vung_mien}" if vung_mien else ''
                    html += f"<br><b>Mô tả:</b> {mo_ta}" if mo_ta else ''
                    if img_url:
                        html += f"<br><img src=\"{img_url}\" alt=\"{ten_mon}\" class='zoomable-img' style='max-width:350px;border-radius:8px;margin:8px 0;cursor:zoom-in;'>"
                    # Gợi ý tiếp các câu hỏi khác nhau
                    suggestions = [
                        "Bạn muốn biết nguyên liệu của món này không?",
                        "Bạn muốn biết cách làm món này không?",
                        "Bạn muốn xem thêm hình ảnh món khác không?",
                        "Bạn muốn tham khảo thêm món ăn khác không?",
                        "Bạn muốn biết món nào phù hợp cho dịp đặc biệt không?",
                        "Bạn muốn hỏi về món ăn vùng miền khác không?"
                    ]
                    html += f"<br><i>{random.choice(suggestions)}</i>"
                    return html
    return None
