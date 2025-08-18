import re

def handle_intent_hinh_anh(user_input, find_best_match):
    """
    Nhận diện các câu hỏi về hình ảnh món ăn, ví dụ: 'ảnh món ...', 'hình món ...', 'xem ảnh ...', 'hình ảnh ...', ...
    """
    patterns = [
        r"(ảnh|hình|hình ảnh|xem ảnh|xem hình)\s*(món)?\s*([\w\sàáảãạâấầẩẫậăắằẳẵặèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\-]+)",
        r"(món)?\s*([\w\sàáảãạâấầẩẫậăắằẳẵặèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\-]+)\s*(ảnh|hình|hình ảnh)"
    ]
    for pat in patterns:
        m = re.search(pat, user_input.lower())
        if m:
            # Lấy tên món từ group dài nhất
            groups = [g for g in m.groups() if g and g not in ["ảnh", "hình", "hình ảnh", "xem ảnh", "xem hình", "món"]]
            ten_mon_query = max(groups, key=len) if groups else None
            if ten_mon_query:
                ten_mon_query = ten_mon_query.strip()
                found, _ = find_best_match(ten_mon_query)
                if found:
                    ten_mon_norm = ten_mon_query.lower().strip()
                    found_mon_norm = found.get('mon_an', '').lower().strip()
                    found_words = set(found_mon_norm.split())
                    query_words = set(ten_mon_norm.split())
                    intersect = found_words & query_words
                    if ten_mon_norm == found_mon_norm or (found_words and query_words and len(intersect)/max(len(found_words),len(query_words))>=0.8):
                        if found.get('hinh_anh'):
                            img_url = found['hinh_anh']
                            ten_mon = found.get('mon_an', ten_mon_query)
                            # Trả về ảnh với class zoomable-img để JS xử lý zoom modal
                            return (
                                f"<b>Hình ảnh món {ten_mon}:</b><br>"
                                f"<img src=\"{img_url}\" alt=\"{ten_mon}\" class='zoomable-img' style='max-width:350px;border-radius:8px;margin:8px 0;cursor:zoom-in;' title='Bấm vào để xem ảnh lớn hơn'>"
                            )
                # Nếu không có ảnh, trả về link Google Image Search
                google_url = f"https://www.google.com/search?tbm=isch&q={ten_mon_query.replace(' ', '+')}"
                return f"Xin lỗi, hiện tại mình chưa có hình ảnh cho món '{ten_mon_query}'. Bạn có thể xem thêm trên Google: <a href=\"{google_url}\" target=\"_blank\">Bấm vào đây để xem hình ảnh món {ten_mon_query}</a>"
    return None
