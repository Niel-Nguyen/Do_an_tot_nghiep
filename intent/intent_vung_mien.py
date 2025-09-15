import re

def handle_intent_vung_mien(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions):
    # Nếu là câu hỏi về cách làm, công thức, chế biến, nấu... thì KHÔNG xử lý ở intent_vung_mien
    if re.search(r"cách[\s_]*(làm|nấu|che bien|chế biến)|cong thuc|công thức|làm[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|nấu[\s_]*(thế nào|sao|như nào|như thế nào|ra sao|kiểu gì|kiểu nào|được không|sao cho ngon|ngon nhất)|hướng dẫn|làm món|nấu món|chế biến món|cach lam|cach nau|cach che bien|cach che bien mon|cach nau mon|cach lam mon|cach che bien|cach che bien mon|cach che bien|cach che bien mon", user_input.lower()):
        return None, None
    # Nhận diện truy vấn về vùng miền với nhiều biến thể
    text = normalize_text(user_input)
    # Hỗ trợ nhiều cách hỏi khác nhau
    patterns = [
        r"mi[eê]n\s*(b[ăa]c|nam|trung)",
        r"m[óo]n\s*(b[ăa]c|nam|trung)",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)m[óo]n",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]n",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]u",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]c",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]i",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]p",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]m",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]t",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]u",
        r"(b[ăa]c|nam|trung)\s*([\w\s]*)[ăa]c",
    ]
    vung = None
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            v = m.group(1)
            if v.startswith("b"):
                vung = "Miền Bắc"
            elif v.startswith("n"):
                vung = "Miền Nam"
            elif v.startswith("t"):
                vung = "Miền Trung"
            break
    if not vung:
        return None, None
    mon_vung_mien_da_tra = set()
    for turn in history:
        if 'mon_vung_mien_suggested' in turn:
            mon_vung_mien_da_tra.update(turn['mon_vung_mien_suggested'])
    filter_vung_mien = {"vung_mien": {"$eq": vung}}
    candidates = search_pinecone(vung, top_k=200, filter_override=filter_vung_mien)
    mon_vung_mien = []
    for doc in candidates:
        if doc.get('vung_mien', '') == vung and doc.get('mon_an', '') not in mon_vung_mien_da_tra:
            mon_vung_mien.append(doc)
    if not mon_vung_mien:
        answer = f"Xin lỗi, hiện mình chưa tìm được món nào của {vung} phù hợp trong dữ liệu nữa."
        mon_vung_mien_suggested = []
    else:
        answer_lines = [f"Một số món ăn của {vung} bạn có thể tham khảo:"]
        mon_vung_mien_suggested = []
        for doc in mon_vung_mien[:7]:
            ten_mon = doc.get('mon_an', '')
            vung_mien_doc = doc.get('vung_mien', '')
            mo_ta = doc.get('mo_ta', '')
            answer_lines.append(f"- {ten_mon} (Vùng miền: {vung_mien_doc}): {mo_ta}")
            mon_vung_mien_suggested.append(ten_mon)
        answer = "\n".join(answer_lines)
    answer += suggest_follow_up_questions()
    return answer, mon_vung_mien_suggested
