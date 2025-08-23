# scripts/prepare_training_data_attribute.py
import json, random, re
import pandas as pd
from pathlib import Path
from collections import defaultdict

random.seed(42)

# === Paths ===
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent                             # .../model_fine_turn_2
EXCEL = ROOT / "scripts" / "data100mon.xlsx"

OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_TRAIN = OUT_DIR / "pairs_attribute_train.jsonl"
OUT_DEV   = OUT_DIR / "pairs_attribute_dev.jsonl"

# === Config (đã rút gọn desc/body để CE tập trung thuộc tính) ===
K_NEG = 10
MAX_DESC = 160          # ↓ ngắn hơn
MAX_INGR = 120
CE_BODY_MAX = 180       # ↓ body ngắn
DEV_RATIO = 0.10
MAX_QUERIES_PER_ITEM = 16

# === Helpers ===
def safe(s):
    if pd.isna(s): return ""
    return str(s).strip()

def normalize_cols(df):
    df.columns = [re.sub(r'\s+', '_', str(c).strip().lower()) for c in df.columns]
    return df

def pick(cols, *names):
    for n in names:
        if n in cols: return n
    return None

def to_float(x):
    try:
        return float(str(x).replace(',', '.'))
    except:
        return None

def clip_text(s, max_chars=300):
    s = s or ""
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:max_chars]

def shorten_words(s, max_words=22):
    """Rút mô tả theo số từ (ổn định hơn theo ký tự)."""
    s = re.sub(r'\s+', ' ', s or "").strip()
    if not s: return ""
    words = s.split(' ')
    if len(words) <= max_words:
        return s
    return ' '.join(words[:max_words]).rstrip('.,;:!') + "…"

def clean_attr(x):
    return safe(x).replace('[','(').replace(']',')')

def join_nonempty(*parts, sep=' '):
    return sep.join([p for p in parts if p])

# === Buckets (giải thích):
# PriceBucket:  <=40k -> 'rẻ' ; <=80k -> 'trung' ;  >80k -> 'nhỉnh'
# TimeBucket :  <=20' -> 'nhanh'; <=40' -> 'trung'; >40' -> 'bận'
def price_bucket(price):
    v = to_float(price)
    if v is None: return ""
    if v <= 40000: return "rẻ"
    if v <= 80000: return "trung"
    return "nhỉnh"

def time_bucket(minutes):
    m = to_float(minutes)
    if m is None: return ""
    m = int(m)
    if m <= 20: return "nhanh"
    if m <= 40: return "trung"
    return "bận"

def protein_desc(p):
    v = to_float(p)
    if v is None: return ""
    if v >= 25: return "giàu đạm"
    if v >= 15: return "đạm ở mức vừa"
    return "nhẹ đạm"

def fat_desc(f):
    v = to_float(f)
    if v is None: return ""
    if v >= 20: return "khá béo"
    if v <= 8:  return "ít béo"
    return "độ béo trung bình"

# === Load Excel ===
assert EXCEL.exists(), f"❌ Không thấy file Excel: {EXCEL}"
df = pd.read_excel(EXCEL)
df = normalize_cols(df)

cands = df.columns.tolist()
col_name   = pick(cands, "name", "ten", "ten_mon", "dish", "mon", "ten_mon_an", "món_ăn", "món_ăn")
col_desc   = pick(cands, "desc", "mo_ta", "description", "dien_giai", "mota", "mô_tả")
col_region = pick(cands, "region", "vung", "mien", "khu_vuc", "vung_mien", "mien_vung", "vùng_miền")
col_mood   = pick(cands, "mood", "tam_trang", "vi_phu_hop", "cam_xuc", "gu", "taste_mood","tâm_trạng","cảm_xúc","tâm_trạng,_cảm_xúc")
col_type   = pick(cands, "type", "loai", "category", "phan_loai", "nhom", "chính/vặt", "chinh/vat")
col_texture= pick(cands, "texture", "ket_cau", "do_mem", "do_gion", "cau_truc", "mouthfeel", "khô/nước", "kho/nuoc")
col_ingredients = pick(cands, "ingredients", "nguyen_lieu", "thanh_phan")
col_recipe = pick(cands, "recipe", "cong_thuc", "cach_nau", "huong_dan_nau", "cách_làm/công_thức")
col_price  = pick(cands, "price", "gia", "giá")
col_unit   = pick(cands, "unit", "don_vi", "đơn_vị_tính")
col_veg    = pick(cands, "veg", "diet", "vegetarian", "chay/mặn", "chay_man")
col_time   = pick(cands, "time", "thoi_gian", "thoi_gian_nau", "cooking_time", "thời_gian_nấu")
col_cal    = pick(cands, "calories", "cal")
col_fat    = pick(cands, "fat")
col_protein= pick(cands, "protein")
col_fiber  = pick(cands, "fiber")
col_sugar  = pick(cands, "sugar")
col_img    = pick(cands, "image", "hinh_anh", "ảnh")

# === Build items (retrieval_text & ce_text) ===
items = []
for _, r in df.iterrows():
    name = safe(r.get(col_name, ""))
    if not name:
        continue

    region   = clean_attr(r.get(col_region, ""))
    mood     = clean_attr(r.get(col_mood, ""))
    typ      = clean_attr(r.get(col_type, ""))
    texture  = clean_attr(r.get(col_texture, ""))
    desc_raw = safe(r.get(col_desc, ""))
    desc     = clip_text(shorten_words(desc_raw, max_words=22), max_chars=MAX_DESC)
    ingred   = clip_text(safe(r.get(col_ingredients, "")), max_chars=MAX_INGR)
    recipe   = ""  # ❗Bỏ công thức khỏi CE_text để giảm noise
    price    = safe(r.get(col_price, ""))
    unit     = safe(r.get(col_unit, ""))
    veg      = clean_attr(r.get(col_veg, ""))
    time     = safe(r.get(col_time, ""))
    cal      = safe(r.get(col_cal, ""))
    fat      = safe(r.get(col_fat, ""))
    protein  = safe(r.get(col_protein, ""))
    fiber    = safe(r.get(col_fiber, ""))
    sugar    = safe(r.get(col_sugar, ""))
    img      = safe(r.get(col_img, ""))

    p_bucket = price_bucket(price)
    t_bucket = time_bucket(time)

    # Retrieval text (dùng cho RAG hiển thị)
    retrieval_text = f"{name}"
    if region:  retrieval_text += f" [Region:{region}]"
    if mood:    retrieval_text += f" [Mood:{mood}]"
    if typ:     retrieval_text += f" [Type:{typ}]"
    if veg:     retrieval_text += f" [Veg:{veg}]"
    if texture: retrieval_text += f" [Texture:{texture}]"
    if p_bucket: retrieval_text += f" [PriceBucket:{p_bucket}]"
    if t_bucket: retrieval_text += f" [TimeBucket:{t_bucket}]"
    if price and unit: retrieval_text += f" [Price:{price} {unit}]"
    if time:    retrieval_text += f" [Time:{time} phút]"
    if cal:     retrieval_text += f" [Calories:{cal}]"
    if fat:     retrieval_text += f" [Fat:{fat}]"
    if protein: retrieval_text += f" [Protein:{protein}]"
    if desc:    retrieval_text += f". {desc}"
    if ingred:  retrieval_text += f" | Ingredients: {ingred}"

    # ===== CE text (TAG đậm ở đầu → Name → mô tả ngắn) =====
    tags = "".join([
        f"[Region: {region or 'unknown'}]",
        f"[Mood: {mood or 'unknown'}]",
        f"[Type: {typ or 'unknown'}]",
        f"[Veg: {veg or 'unknown'}]",
        f"[Texture: {texture or 'unknown'}]",
        f"[PriceBucket: {p_bucket or 'unknown'}]",
        f"[TimeBucket: {t_bucket or 'unknown'}]",
    ])
    # Name line rõ ràng để inference hiển thị đúng
    name_line = f"Món ăn: {name}"
    # Body cực ngắn
    body_bits = []
    if desc:   body_bits.append(f"Mô tả: {desc}.")
    # (tuỳ chọn) điểm dinh dưỡng ngắn gọn
    pf = protein_desc(protein)
    ff = fat_desc(fat)
    nut = " ".join([x for x in [pf, ff] if x])
    if nut:
        body_bits.append(nut.capitalize() + ".")
    body = clip_text(" ".join(body_bits), max_chars=CE_BODY_MAX)

    ce_text = join_nonempty(tags, name_line, body, sep="\n").strip()

    items.append({
        "name": name, "region": region, "mood": mood, "type": typ,
        "texture": texture, "veg": veg, "unit": unit, "price": price,
        "price_bucket": p_bucket, "time_bucket": t_bucket,
        "time": time, "desc": desc, "ingredients": ingred, "recipe": recipe,
        "nutrition": {"cal":cal, "fat":fat, "protein":protein, "fiber":fiber, "sugar":sugar},
        "image": img,
        "retrieval_text": retrieval_text,
        "ce_text": ce_text
    })

# === Negatives (ưu tiên hard negatives: cùng Region/Type/Veg nhưng khác Mood/Texture) ===
def _norm(s): return (s or "").strip().lower()

def _veg_bucket(s):
    t = _norm(s)
    if "chay" in t or "veg" in t or "vegetarian" in t: return "chay"
    if "mặn" in t or "man" in t or "meat" in t: return "man"
    return ""

def contrast_negatives(target, pool, k=K_NEG):
    treg, tmood, ttype = _norm(target["region"]), _norm(target["mood"]), _norm(target["type"])
    tveg = _veg_bucket(target["veg"])
    ttex = _norm(target["texture"])

    hard_strict, hard_loose, opposites, others = [], [], [], []
    for it in pool:
        if it["name"] == target["name"]:
            continue
        reg_it, mood_it, type_it = _norm(it["region"]), _norm(it["mood"]), _norm(it["type"])
        veg_it = _veg_bucket(it["veg"])
        tex_it = _norm(it["texture"])

        same_reg  = treg and reg_it == treg
        same_type = ttype and type_it == ttype
        same_veg  = tveg and veg_it == tveg
        diff_mood = tmood and mood_it and mood_it != tmood
        diff_tex  = ttex and tex_it and tex_it != ttex

        # strict: khớp >=2 trụ cột (Region/Type/Veg) nhưng khác mood/texture
        same_core = sum([same_reg, same_type, same_veg])
        if same_core >= 2 and (diff_mood or diff_tex):
            hard_strict.append(it["ce_text"])
            continue

        # loose: khớp ít nhất 1 trụ cột
        if same_core >= 1:
            hard_loose.append(it["ce_text"])
            continue

        # opposites: khác rõ ràng một trong các core tags
        reg_diff  = treg  and reg_it  and reg_it  != treg
        type_diff = ttype and type_it and type_it != ttype
        veg_diff  = tveg  and veg_it  and veg_it  != tveg
        if reg_diff or type_diff or veg_diff:
            opposites.append(it["ce_text"])
        else:
            others.append(it["ce_text"])

    random.shuffle(hard_strict); random.shuffle(hard_loose)
    random.shuffle(opposites);   random.shuffle(others)

    result = []
    for src in (hard_strict, hard_loose, opposites, others):
        for x in src:
            if len(result) >= k:
                break
            result.append(x)
        if len(result) >= k:
            break
    return result[:k]

# === Query generator: chỉ sinh dựa trên thuộc tính thật (boost nhóm yếu Bắc/vặt) ===
def gen_queries(it):
    qs = []
    reg, mood, typ, veg = it["region"], it["mood"], it["type"], it["veg"]
    price, time = it["price"], it["time"]
    p_b, t_b = it.get("price_bucket",""), it.get("time_bucket","")
    prot, fat = it["nutrition"]["protein"], it["nutrition"]["fat"]

    base = ["Gợi ý", "Đề xuất", "Cho mình", "Mình muốn tìm", "Tư vấn giúp"]
    # Boost nhẹ cho miền 'Bắc' và type 'vặt'
    if _norm(reg) == "bắc":
        base = base + ["Cho tôi", "Tìm giúp"]  # +2 biến thể
    if _norm(typ) in ("vặt", "vat"):
        base = base + ["Có món vặt nào", "Ăn chơi"]  # +2 biến thể

    if reg:   qs += [f"{b} món miền {reg}" for b in base]
    if mood:  qs += [f"{b} món hợp tâm trạng {mood}" for b in base]
    if typ:   qs += [f"{b} món {typ}" for b in base]
    if veg:   qs += [f"{b} món {veg.lower()}" for b in base]
    if t_b == "nhanh": qs += [f"{b} món nấu nhanh" for b in base]
    if t_b == "trung": qs += [f"{b} món nấu khoảng 20–40 phút" for b in base]
    if t_b == "bận":  qs += [f"{b} món dành cho lúc rảnh (không gấp)" for b in base]
    if prot:  qs += [f"{b} món nhiều đạm" for b in base]
    if fat:   qs += [f"{b} món ít béo" for b in base]
    if p_b == "rẻ":   qs += [f"{b} món giá dễ chịu" for b in base]
    if p_b == "trung":qs += [f"{b} món giá trung bình" for b in base]
    if p_b == "nhỉnh":qs += [f"{b} món ngân sách rộng" for b in base]

    # Biến thể không dấu – hạn chế số lượng để tránh noise
    ascii_map = [
        (r'[đĐ]', 'd'),
        (r'[áàảãạâấầẩẫậăắằẳẵặÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶ]', 'a'),
        (r'[éèẻẽẹêếềểễệÉÈẺẼẸÊẾỀỂỄỆ]', 'e'),
        (r'[óòỏõọôốồổỗộơớờởỡợÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]', 'o'),
        (r'[íìỉĩịÍÌỈĨỊ]', 'i'),
        (r'[úùủũụưứừửữựÚÙỦŨỤƯỨỪỬỮỰ]', 'u'),
        (r'[ýỳỷỹỵÝỲỶỸỴ]', 'y'),
    ]
    extra = []
    for q in qs[:5]:
        q1 = q
        for pat, rep in ascii_map:
            q1 = re.sub(pat, rep, q1)
        extra.append(q1)
    qs += extra

    qs = list(dict.fromkeys([q.strip() for q in qs if q.strip()]))
    random.shuffle(qs)
    return qs[:MAX_QUERIES_PER_ITEM]

# === Build all rows ===
all_rows = []
for it in items:
    queries = gen_queries(it)
    for q in queries:
        negs = contrast_negatives(it, items, k=K_NEG)
        if not negs:
            continue
        rec = {
            "query": q,
            "positive": it["ce_text"],
            "negatives": negs,
            "meta": {
                "name": it["name"],
                "desc": it["desc"],
                "ingredients": it["ingredients"],
                "recipe": it["recipe"],
                "price": it["price"], "unit": it["unit"],
                "price_bucket": it.get("price_bucket",""),
                "time_bucket": it.get("time_bucket",""),
                "region": it["region"], "mood": it["mood"], "type": it["type"],
                "veg": it["veg"], "texture": it["texture"],
                "time": it["time"], "image": it["image"],
                "nutrition": it["nutrition"],
                "retrieval_text": it["retrieval_text"],
                "ce_text": it["ce_text"]
            }
        }
        all_rows.append(rec)

random.shuffle(all_rows)

# === Stratified-ish split theo (Region, Type, Veg) ===
groups = defaultdict(list)
def key_of(rec):
    m = rec.get("meta", {})
    reg = (m.get("region") or "unknown").strip().lower()
    typ = (m.get("type") or "unknown").strip().lower()
    veg = (m.get("veg") or "unknown").strip().lower()
    return f"R:{reg}|T:{typ}|V:{veg}"

for r in all_rows:
    groups[key_of(r)].append(r)

dev_rows, train_rows = [], []
for gkey, lst in groups.items():
    random.shuffle(lst)
    n = max(1, int(round(len(lst) * DEV_RATIO)))
    dev_rows.extend(lst[:n])
    train_rows.extend(lst[n:])

# — Điều chỉnh nhẹ nếu lệch do làm tròn
if len(dev_rows) == 0 and len(train_rows) > 1:
    dev_rows.append(train_rows.pop())
elif len(dev_rows) > len(all_rows) * (DEV_RATIO + 0.1):
    surplus = len(dev_rows) - int(len(all_rows) * DEV_RATIO)
    train_rows.extend(dev_rows[-surplus:])
    dev_rows = dev_rows[:-surplus]

with open(OUT_TRAIN, "w", encoding="utf-8") as ftr:
    for r in train_rows:
        ftr.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(OUT_DEV, "w", encoding="utf-8") as fdv:
    for r in dev_rows:
        fdv.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"✅ Saved train: {OUT_TRAIN} | Rows: {len(train_rows)}")
print(f"✅ Saved dev  : {OUT_DEV}   | Rows: {len(dev_rows)}")
print(f"ℹ️  Negatives per query (k) = {K_NEG}, DEV_RATIO={DEV_RATIO}")
print("ℹ️  DEV split theo khóa (Region,Type,Veg):")
for gkey in sorted(groups.keys()):
    n_total = len(groups[gkey])
    n_dev_est = max(1, int(round(n_total * DEV_RATIO)))
    print(f"   - {gkey}: total={n_total}, dev≈{n_dev_est}")
