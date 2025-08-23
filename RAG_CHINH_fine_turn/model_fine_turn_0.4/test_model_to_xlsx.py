# -*- coding: utf-8 -*-
# Chỉ dùng kết quả từ model đã fine-tune (CrossEncoder) để sinh câu trả lời.
# answer = passage trong corpus có điểm cao nhất theo model (không heuristic).

from sentence_transformers import CrossEncoder
import json, pandas as pd, sys
from pathlib import Path

# ====== ĐƯỜNG DẪN THEO ZIP ======
BASE_DIR    = Path(r"d:\model_fine_turn")
MODEL_DIR   = BASE_DIR / "models" / "reranker_food"
CORPUS_PATH = BASE_DIR / "data" / "corpus.jsonl"
OUT_XLSX    = BASE_DIR / "test_results.xlsx"

# ====== DANH SÁCH CÂU HỎI (NGUYÊN VĂN BẠN GỬI) ======
RAW_QUESTIONS = r"""
1	Gợi ý cho tôi món ngon miền Bắc
1	Tôi muốn ăn món chay hôm nay
3	Cho tôi vài món hợp tiết trời lạnh
4	Món nào cay và ngon nhất ở miền Trung?
5	Gợi ý món ăn vặt miền Nam
6	Tôi đang muốn ăn món lẩu, có gợi ý không?
7	Cho tôi gợi ý vài món chính miền Trung
8	Có món nào ít calo không?
9	Tôi muốn ăn món hải sản
10	Món ăn miền Bắc nào hợp ăn với cơm?
11	Món nào có thể ăn vào mùa hè cho mát?
12	Cho tôi vài món súp ở miền Trung
13	Gợi ý món miền Nam cho bữa tiệc
14	Món ăn nào hợp với tâm trạng thư giãn?
15	Tôi cần vài món cho người ăn kiêng chất béo
16	Có món ăn nào vừa nhanh vừa ngon không?
17	Món mặn miền Bắc nào phổ biến nhất?
18	Tôi muốn tìm món có vị chua
19	Món nào giàu protein nhất?
20	Gợi ý vài món ăn với bún
21	Tôi đang muốn ăn món chính miền Nam
22	Có món chay nào có nấm không?
23	Món ăn hợp với tiết trời se lạnh
24	Tôi muốn ăn nhẹ, có món nào không nhiều đường?
25	Có món nào cuốn (wrap) không?
26	Món nào nhiều màu sắc đẹp mắt?
27	Gợi ý vài món ăn khô miền Trung
28	Món ăn vặt nào giàu chất xơ?
30	Tôi thích món thanh đạm, có gợi ý nào không?
31	Món nào có nguyên liệu là mực ống?
32	Cho tôi các món có tôm sú
33	Món nào cần cá ngừ tươi?
34	Tìm món có nguyên liệu là thịt ba chỉ
35	Tôi muốn ăn món có bún tươi
36	Món nào dùng cá chim?
37	Tìm món có trứng muối
38	Món nào có nguyên liệu là khoai lang?
39	Cho tôi món có lá lốt
40	có món nào dùng với mắn nêm không?
41	Tôi muốn tìm món có nấm đông cô
42	Món có rau răm là gì?
43	Món nào dùng đậu hũ ky?
44	Tìm món có sả băm
45	Món nào có gừng tươi?
46	Cho tôi các món có khoai tây
47	Món nào cần cà tím?
48	Tôi muốn ăn món có đậu phộng rang
49	Món nào có chao trắng?
50	Món nào có thịt vịt xiêm?
51	Tìm món có cá lóc
52	Cho tôi món có nước dừa tươi
53	Món nào có cải thìa
54	Tôi muốn các món có cà chua bi
55	Món nào có phô mai
56	Giá của món Mực ống hấp củ đậu là bao nhiêu?
57	Giá của món Chả giò ngũ vị là bao nhiêu?
58	Giá của món Canh ba màu là bao nhiêu?
59	Giá của món Tàu hủ ky chiên xả ớt là bao nhiêu?
60	Giá của món Gỏi ngó sen tôm thịt là bao nhiêu?
61	Giá của món Bánh tráng cuốn xốt Mayo là bao nhiêu?
62	Giá của món Gỏi Cuốn Tôm Chua là bao nhiêu?
63	Giá của món Bún Mắm Heo Quay là bao nhiêu?
64	Giá của món Gỏi mít thịt ba chỉ là bao nhiêu?
65	Giá của món Cuốn chả tôm là bao nhiêu?
66	Giá của món Mực ống hấp củ đậu là bao nhiêu?
67	Giá của món Chả giò ngũ vị là bao nhiêu?
68	Giá của món Canh ba màu là bao nhiêu?
69	Giá của món Tàu hủ ky chiên xả ớt là bao nhiêu?
70	Giá của món Gỏi ngó sen tôm thịt là bao nhiêu?
71	Giá món Bánh tráng cuốn xốt Mayo bao nhiêu tiền?
72	Giá món Gỏi Cuốn Tôm Chua là bao nhiêu?
73	Giá món Bún Mắm Heo Quay bao nhiêu?
74	Giá món Gỏi mít thịt ba chỉ?
101	Tôi muốn đặt món Mực ống hấp củ đậu
102	Đặt cho tôi 2 phần Chả giò ngũ vị
103	Cho tôi đặt 3 phần Canh ba màu
104	Tôi muốn gọi món Tàu hủ ky chiên xả ớt
105	Đặt dùm tôi 1 phần Gỏi ngó sen tôm thịt
106	Cho tôi gọi 5 phần Bánh tráng cuốn xốt Mayo
107	Tôi muốn ăn Gỏi Cuốn Tôm Chua, đặt giúp tôi 2 phần
108	Mình đặt 4 phần Bún Mắm Heo Quay nhé
109	Cho 2 suất Gỏi mít thịt ba chỉ
110	Tôi order 3 tô Cuốn chả tôm
111	Gọi giúp tôi 1 phần Gỏi gà sứa sả tắc
112	Đặt một suất Bún Cá Ngừ
113	Tôi muốn gọi 2 phần Ba Rọi Xông Khói Cuộn Phô Mai Áp Chảo
114	Đặt cho tôi 1 tô Bún Cá Rô
115	Cho tôi 3 dĩa Cá chiên bông điên điển
116	Mình cần 2 phần Gà nướng lá húng lủi
117	Book giúp tôi 1 phần Chả Lụa Chay
118	Order 4 phần Càng cua chiên mè xốt Mayo
119	Đặt thêm 2 phần Mì vịt tiềm chay
120	Cho 1 phần Canh chua cá củ thì là
121	Gọi 5 phần Chả cá Lã Vọng
122	Đặt một phần Bún bò bắp cải chua
123	Mình order 1 phần Canh mồng tơi bắp nụ
124	Cho tôi 2 tô Lẩu hoa cá kèo
125	Đặt 3 phần Chả giò hàu
126	Hủy món Gỏi rau mầm tôm tôi vừa đặt
127	Tôi muốn hủy 2 phần Chả giò ngũ vị
128	Hủy giúp tôi toàn bộ món Bún Mắm Heo Quay
129	Thay món Gỏi mít thịt ba chỉ bằng Gỏi gà sứa sả tắc
130	Sửa số lượng Cuốn chả tôm từ 3 tô xuống còn 1 tô
131	Mình muốn đổi món Bánh tráng cuốn xốt Mayo thành Gỏi Cuốn Tôm Chua
132	Hủy tất cả món tôi đặt lúc nãy
133	Thêm 1 phần nữa vào món Ba Rọi Xông Khói Cuộn Phô Mai đã đặt
134	Giảm số lượng Bún bò bắp cải chua từ 2 xuống 0
135	Bỏ món Canh chua cá củ thì là khỏi đơn
136	Tôi muốn thay Gà nướng lá húng lủi bằng Càng cua chiên mè xốt Mayo
137	Sửa đơn hàng: thêm 1 phần Ba Rọi Xông Khói Cuộn Phô Mai
138	Hủy 1 phần Chả Lụa Chay ra khỏi đơn
139	Bỏ món Gỏi gà sứa sả tắc
140	Đổi món Chả giò hàu thành Lẩu hoa cá kèo
141	Tính tiền đơn hàng này giúp tôi
143	Thanh toán hết tất cả món vừa đặt
144	Cho tôi xem lại hóa đơn chi tiết
145	Tôi sẽ chuyển khoản qua Internet Banking
146	Tính tiền giúp tôi
147	Cho tôi xem hóa đơn
156	Thanh toán một phần hóa đơn
157	Cho tôi biết số tiền cần trả
159	Thanh toán ngay tất cả các món đã đặt
160	chuyển khoản
161	Toi muon an mon Muc ong hap cu dau
162	GỢI Ý mốnn ngon miền bắccc
163	Cho tôi 🍜 món bún bò Huế
164	Tôi muốn ăn “goi ngo sen tom”
165	Giá món 🍤 Gỏi Cuốn Tôm Chua là bao nhiêu
166	How much is Mực trứng xào rau răm?
167	🇯🇵 ラーメンが食べたい
168	Tôi muỗn ănn Bún mắm Heo Qyay
169	Hủy món “Chả Lụa Chay” plz
170	Pay by momo please
171	Muốn ăn món cay miền trung
172	Tôi muốn món protein cao nhất
173	Đăt 2 phan Banh trang cuon xot Mayo
174	Hủy 1 mon Bun Ca ngu nha
175	Bill please
176	Tôi muốn ăn món 🍲 miền Nam mùa tết
177	Gợi ý món chay có nấm 🍄
178	价格 của món Gỏi gà sứa sả tắc là bao nhiêu?
179	Order for me: 2 Goi mit thit ba chi
180	Tôi muốn ăn món 😋 Canh chua cá củ thì là
181	Tôi đang buồn, có món nào an ủi không?
182	Tôi thấy rất vui, gợi ý món nhé!
183	Hôm nay trời lạnh, muốn ăn món ấm áp
184	Tôi thấy mệt, có món nào thư giãn không?
185	Ngày mới bắt đầu, tôi rất hào hứng
186	Tôi cần món ăn tạo cảm giác nhẹ nhàng
187	Tôi muốn thưởng thức món ăn vui vẻ 🤩
188	Có món nào phù hợp để thư giãn buổi tối không?
189	Hôm nay tôi muốn ăn món ấm cúng bên gia đình
190	Thời tiết đẹp, tôi cảm thấy hào hứng
191	Tôi thấy chán, muốn ăn món nhẹ bụng
192	Tôi muốn ăn món giúp tinh thần phấn khởi
193	Buồn ngủ quá, có món nào thư giãn không?
194	Món nào làm mình cảm thấy ấm áp hơn?
195	Tôi cảm thấy đầy năng lượng, có món nào hợp?
196	Món nào ăn vào cảm thấy yêu đời hơn?
197	Món nào hợp với tâm trạng thư giãn sau làm việc?
198	Tôi đang chill, muốn ăn món nhẹ nhàng
199	Món nào miền bắc, phù hợp khi quây quần?
200	Tôi muốn ăn món giúp tôi Hào hứng hơn, tôi muốn món này là món canh miền trung
""".strip()

# ====== HÀM PHỤ ======
def parse_questions(raw: str):
    qs = []
    for line in raw.splitlines():
        if not line.strip(): continue
        parts = line.split("\t", 1)
        q = parts[1] if len(parts) == 2 else parts[0]
        qs.append(q.strip())
    return qs

def load_corpus(path: Path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            obj = json.loads(line)
            passage = obj.get("passage") or obj.get("desc") or obj.get("name","")
            obj["passage"] = passage
            rows.append(obj)
    return rows

# ====== KIỂM TRA FILE ======
if not MODEL_DIR.exists(): sys.exit(f"[ERROR] Không thấy model folder: {MODEL_DIR}")
if not (MODEL_DIR/"config.json").exists(): sys.exit("[ERROR] Thiếu config.json trong model folder")
if not CORPUS_PATH.exists(): sys.exit(f"[ERROR] Không thấy corpus.jsonl: {CORPUS_PATH}")

# ====== NẠP MODEL ======
model = CrossEncoder(MODEL_DIR.as_posix(), device="cpu", local_files_only=True)

# ====== NẠP CORPUS & QUESTIONS ======
corpus = load_corpus(CORPUS_PATH)
questions = parse_questions(RAW_QUESTIONS)

# ====== TEST: chọn passage điểm cao nhất làm answer ======
def batched(iterable, batch_size):
    n = len(iterable)
    for i in range(0, n, batch_size):
        yield iterable[i:i+batch_size]

answers = []
BATCH = 256
for q in questions:
    pairs = [[q, r["passage"]] for r in corpus]
    scores_all = []
    for chunk in batched(pairs, BATCH):
        scores_all.extend(model.predict(chunk))
    best_idx = max(range(len(scores_all)), key=lambda i: scores_all[i])
    best_row = corpus[best_idx]
    answers.append(best_row["passage"])

# ====== XUẤT EXCEL ======
df = pd.DataFrame({"question": questions, "answer": answers})
df.to_excel(OUT_XLSX, index=False)
print(f"[OK] Đã xuất file: {OUT_XLSX}")