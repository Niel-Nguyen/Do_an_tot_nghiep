import re

def handle_intent_contact(user_input):
    """
    Nhận diện các câu hỏi về địa chỉ, số điện thoại, website, liên hệ, hotline...
    """
    patterns = [
        r"địa chỉ|ở đâu|chỗ nào|address",
        r"số điện thoại|hotline|liên hệ|phone|liên lạc",
        r"website|trang web|web site|trang chủ|web của (bạn|nhà hàng)",
        r"giờ mở cửa|giờ hoạt động|mấy giờ|thời gian hoạt động",
        r"chỉ đường|đường đi|tới nhà hàng|đến nhà hàng|map|bản đồ"
    ]
    contact_info = (
        "Nhà hàng Phúc Đẹp Chai xin gửi bạn thông tin liên hệ:\n"
        "- Địa chỉ: Quy Nhơn, Bình Định\n"
        "- Hotline: 03.8228.5747\n"
        "- Website: <a href=\"https://www.facebook.com/TM.PhucSay/\" target=\"_blank\">Bấm vào đây để xem website</a>\n"
        "- Chỉ đường: <a href=\"https://www.google.com/maps?q=13.756361,109.154163\" target=\"_blank\">Bấm vào đây để xem bản đồ Google Maps</a>"
    )
    for pat in patterns:
        if re.search(pat, user_input, re.IGNORECASE):
            return contact_info
    return None
