# scripts/prepare_training_data_attribute.py
# -*- coding: utf-8 -*-
"""
Sinh (query, positive, negatives) cho CrossEncoder RERANKER.
- Dùng tất cả thuộc tính trừ 'Cách làm/công thức'
- ce_text giờ có đầy đủ tag: Region/Mood/Type/Veg/Texture + Price/Unit/Time + Cal/Prot/Fat/Fib/Sug
- Body có mô tả ngắn + ING: (nguyên liệu rút gọn)
"""

import json, random, re, argparse, os
import pandas as pd
from pathlib import Path
from collections import defaultdict

random.seed(42)

# ========= Paths & Args =========
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_EXCEL = ROOT / "scripts" / "data100mon.xlsx"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--excel", type=str, default=os.getenv("DATA_XLSX", str(DEFAULT_EXCEL)))
    p.add_argument("--out-train", type=str, default=str(DATA_DIR / "pairs_attribute_train.jsonl"))
    p.add_argument("--out-dev",   type=str, default=str(DATA_DIR / "pairs_attribute_dev.jsonl"))
    p.add_argument("--dev-ratio", type=float, default=0.10)
    p.add_argument("--k-neg", type=int, default=10)
    # các ngưỡng rút gọn
    p.add_argument("--max-desc-words", type=int, default=22)
    p.add_argument("--max-ingr-chars", type=int, default=120)
    p.add_argument("--max-ingr-in-ce", type=int, default=60)   # nguyên liệu hiển thị trong CE
    p.add_argument("--ce-body-max", type=int, default=180)
    p.add_argument("--tag-line-max", type=int, default=260)    # tăng nhẹ để chứa đủ tag số liệu
    p.add_argument("--max-queries-per-item", type=int, default=16)
    return p.parse_args()

# ========= Helpers =========
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

def clip_chars(s, n):
    s = re.sub(r'\s+', ' ', (s or "")).strip()
    return s[:n]

def shorten_words(s, max_words):
    s = re.sub(r'\s+', ' ', (s or "")).strip()
    if not s: return ""
    w = s.split(' ')
    if len(w) <= max_words: return s
    return ' '.join(w[:max_words]).rstrip('.,;:!') + "…"

def clean_attr(x):
    return safe(x).replace('[','(').replace(']',')')

def cut_to_max(s, max_chars):
    s = s or ""
    return s if len(s) <= max_chars else (s[:max_chars-1] + "…")

# ========= Buckets =========
def price_bucket(price):
    v = to_float(price)
    if v is None: return ""
    if v <= 40000: return "rẻ"
    if v <= 80000: return "trung"
    return "nhỉnh"

def time_bucket(minutes):
    v = to_float(minutes)
    if v is None: return ""
    v = int(v)
    if v <= 20: return "nhanh"
    if v <= 40: return "trung"
    return "bận"

def protein_desc(p):
    v = to_float(p)
    if v is None: return ""
    if v >= 25: return "giàu đạm"
    if v >= 15: return "đạm vừa"
    return "nhẹ đạm"

def fat_desc(f):
    v = to_float(f)
    if v is None: return ""
    if v >= 20: return "khá béo"
    if v <= 8:  return "ít béo"
    return "béo trung bình"

# ========= Negative mining =========
def _norm(s): return (s or "").strip().lower()

def _veg_bucket(s):
    t = _norm(s)
    if "chay" in t or "veg" in t or "vegetarian" in t: return "chay"
    if "mặn" in t or "man" in t or "meat" in t: return "man"
    return ""

def contrast_negs(target, pool, k):
    treg, tmood, ttype = _norm(target["region"]), _norm(target["mood"]), _norm(target["type"])
    tveg, ttex = _veg_bucket(target["veg"]), _norm(target["texture"])

    hard_strict, hard_loose, opposites, others = [], [], [], []
    for it in pool:
        if it["name"] == target["name"]: continue
        reg_it, mood_it, type_it = _norm(it["region"]), _norm(it["mood"]), _norm(it["type"])
        veg_it, tex_it = _veg_bucket(it["veg"]), _norm(it["texture"])

        same_reg  = treg and reg_it == treg
        same_type = ttype and type_it == ttype
        same_veg  = tveg and veg_it == tveg
        diff_mood = tmood and mood_it and mood_it != tmood
        diff_tex  = ttex and tex_it and tex_it != ttex
        same_core = sum([same_reg, same_type, same_veg])

        if same_core >= 2 and (diff_mood or diff_tex):
            hard_strict.append(it["ce_text"]); continue
        if same_core >= 1:
            hard_loose.append(it["ce_text"]);  continue

        reg_diff  = treg  and reg_it  and reg_it  != treg
        type_diff = ttype and type_it and type_it != ttype
        veg_diff  = tveg  and veg_it  and veg_it  != tveg
        if reg_diff or type_diff or veg_diff:
            opposites.append(it["ce_text"])
        else:
            others.append(it["ce_text"])

    random.shuffle(hard_strict); random.shuffle(hard_loose)
    random.shuffle(opposites);   random.shuffle(others)

    out = []
    for src in (hard_strict, hard_loose, opposites, others):
        for x in src:
            if len(out) >= k: break
            out.append(x)
        if len(out) >= k: break
    return out[:k]

# ========= Query generator =========
ASCII_MAP = [
    (r'[đĐ]', 'd'),
    (r'[áàảãạâấầẩẫậăắằẳẵặÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶ]', 'a'),
    (r'[éèẻẽẹêếềểễệÉÈẺẼẸÊẾỀỂỄỆ]', 'e'),
    (r'[óòỏõọôốồổỗộơớờởỡợÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]', 'o'),
    (r'[íìỉĩịÍÌỈĨỊ]', 'i'),
    (r'[úùủũụưứừửữựÚÙỦŨỤƯỨỪỬỮỰ]', 'u'),
    (r'[ýỳỷỹỵÝỲỶỸỴ]', 'y'),
]

def gen_queries(it, max_q=16):
    qs = []
    reg, mood, typ, veg = it["region"], it["mood"], it["type"], it["veg"]
    p_b, t_b = it.get("price_bucket",""), it.get("time_bucket","")
    prot, fat = it["nutrition"]["protein"], it["nutrition"]["fat"]

    base = ["Gợi ý", "Đề xuất", "Cho mình", "Mình muốn tìm", "Tư vấn giúp"]
    if _norm(reg) == "bắc": base += ["Cho tôi", "Tìm giúp"]
    if _norm(typ) in ("vặt", "vat"): base += ["Có món vặt nào", "Ăn chơi"]

    if reg:   qs += [f"{b} món miền {reg}" for b in base]
    if mood:  qs += [f"{b} món hợp tâm trạng {mood}" for b in base]
    if typ:   qs += [f"{b} món {typ}" for b in base]
    if veg:   qs += [f"{b} món {veg.lower()}" for b in base]
    if t_b == "nhanh": qs += [f"{b} món nấu nhanh" for b in base]
    if t_b == "trung": qs += [f"{b} món nấu 20–40 phút" for b in base]
    if t_b == "bận":  qs += [f"{b} món không gấp" for b in base]
    if prot:  qs += [f"{b} món nhiều đạm" for b in base]
    if fat:   qs += [f"{b} món ít béo" for b in base]
    if p_b == "rẻ":   qs += [f"{b} món giá dễ chịu" for b in base]
    if p_b == "trung":qs += [f"{b} món giá trung bình" for b in base]
    if p_b == "nhỉnh":qs += [f"{b} món ngân sách rộng" for b in base]

    extras = []
    for q in qs[:5]:
        q1 = q
        for pat, rep in ASCII_MAP:
            q1 = re.sub(pat, rep, q1)
        extras.append(q1)
    qs += extras

    qs = list(dict.fromkeys([q.strip() for q in qs if q.strip()]))
    random.shuffle(qs)
    return qs[:max_q]

# ========= Main =========
def main():
    args = parse_args()
    excel_path = Path(args.excel)
    assert excel_path.exists(), f"❌ Không thấy Excel: {excel_path}"

    df = pd.read_excel(excel_path)
    df = normalize_cols(df)
    cols = df.columns.tolist()

    # map cột
    col_name   = pick(cols, "món_ăn","mon_an","name","ten","ten_mon","dish")
    col_region = pick(cols, "vùng_miền","vung_mien","region","mien","khu_vuc")
    col_ingred = pick(cols, "nguyên_liệu","nguyen_lieu","ingredients")
    col_desc   = pick(cols, "mô_tả","mo_ta","description","desc")
    col_price  = pick(cols, "giá","gia","price")
    col_unit   = pick(cols, "đơn_vị_tính","don_vi_tinh","don_vi","unit")
    col_mood   = pick(cols, "tâm_trạng,_cảm_xúc","tâm_trạng","cam_xuc","mood")
    col_type   = pick(cols, "chính/vặt","chinh/vat","type","phan_loai","category")
    col_tex    = pick(cols, "khô/nước","kho/nuoc","texture","ket_cau")
    col_img    = pick(cols, "hình_ảnh","hinh_anh","image")
    col_veg    = pick(cols, "chay/mặn","chay_man","veg","vegetarian","diet")
    col_time   = pick(cols, "thời_gian_nấu","thoi_gian_nau","time","cooking_time")
    col_cal    = pick(cols, "calories","cal")
    col_fat    = pick(cols, "fat")
    col_fiber  = pick(cols, "fiber")
    col_sugar  = pick(cols, "sugar")
    col_prot   = pick(cols, "protein")
    # recipe/cách làm: cố ý bỏ

    items = []
    for _, r in df.iterrows():
        name = safe(r.get(col_name, ""))
        if not name: continue

        region = clean_attr(r.get(col_region, ""))
        mood   = clean_attr(r.get(col_mood, ""))
        typ    = clean_attr(r.get(col_type, ""))
        veg    = clean_attr(r.get(col_veg, ""))
        tex    = clean_attr(r.get(col_tex, ""))

        desc   = shorten_words(safe(r.get(col_desc, "")), args.max_desc_words)
        ingred = clip_chars(safe(r.get(col_ingred, "")), args.max_ingr_chars)
        price  = safe(r.get(col_price, ""))
        unit   = safe(r.get(col_unit, ""))
        time   = safe(r.get(col_time, ""))
        cal    = safe(r.get(col_cal, ""))
        fat    = safe(r.get(col_fat, ""))
        fiber  = safe(r.get(col_fiber, ""))
        sugar  = safe(r.get(col_sugar, ""))
        prot   = safe(r.get(col_prot, ""))
        img    = safe(r.get(col_img, ""))

        p_bucket = price_bucket(price)
        t_bucket = time_bucket(time)

        # retrieval_text (debug/hiển thị)
        retrieval = name
        for tag in [
            ("Region", region), ("Mood", mood), ("Type", typ), ("Veg", veg),
            ("Texture", tex), ("PriceBucket", p_bucket), ("TimeBucket", t_bucket)
        ]:
            if tag[1]:
                retrieval += f" [{tag[0]}:{tag[1]}]"
        if price and unit: retrieval += f" [Price:{price} {unit}]"
        if time: retrieval += f" [Time:{time} phút]"
        for k, v in [("Calories", cal), ("Fat", fat), ("Protein", prot)]:
            if v: retrieval += f" [{k}:{v}]"
        if desc:   retrieval += f". {desc}"
        if ingred: retrieval += f" | Ingredients: {ingred}"

        # ======== ce_text (đủ tag) ========
        # dòng TAGS: thêm Price/Unit/Time + Cal/Prot/Fat/Fib/Sug (gọn)
        tags = " ".join(filter(None, [
            f"[Region:{region or 'unknown'}]",
            f"[Mood:{mood or 'unknown'}]",
            f"[Type:{typ or 'unknown'}]",
            f"[Veg:{veg or 'unknown'}]",
            f"[Texture:{tex or 'unknown'}]",
            f"[PriceBucket:{p_bucket or 'unknown'}]",
            f"[TimeBucket:{t_bucket or 'unknown'}]",
            f"[Price:{price}]" if price else "",
            f"[Unit:{unit}]" if unit else "",
            f"[Time:{time}]" if time else "",
            f"[Cal:{cal}]" if cal else "",
            f"[Prot:{prot}]" if prot else "",
            f"[Fat:{fat}]" if fat else "",
            f"[Fib:{fiber}]" if fiber else "",
            f"[Sug:{sugar}]" if sugar else "",
        ]))
        tags = cut_to_max(tags, args.tag_line_max)

        name_line = f"Món ăn: {name}"

        body_bits = []
        if desc: body_bits.append(f"Mô tả: {desc}.")
        # ING: rút gọn cho CE
        if ingred:
            body_bits.append(f"ING: {clip_chars(ingred, args.max_ingr_in_ce)}.")
        # verbalize ngắn dinh dưỡng
        pf = protein_desc(prot); ff = fat_desc(fat)
        nut = " ".join([x for x in [pf, ff] if x]).capitalize()
        if nut: body_bits.append(nut + ".")
        body = clip_chars(" ".join(body_bits), args.ce_body_max)

        ce_text = "\n".join([tags, name_line, body]).strip()

        items.append({
            "name": name, "region": region, "mood": mood, "type": typ,
            "veg": veg, "texture": tex, "unit": unit, "price": price,
            "price_bucket": p_bucket, "time_bucket": t_bucket,
            "time": time, "desc": desc, "ingredients": ingred,
            "nutrition": {"cal":cal, "fat":fat, "protein":prot, "fiber":fiber, "sugar":sugar},
            "image": img,
            "retrieval_text": retrieval,
            "ce_text": ce_text
        })

    # build rows
    all_rows = []
    for it in items:
        queries = gen_queries(it, max_q=parse_args().max_queries_per_item)
        for q in queries:
            negs = contrast_negs(it, items, k=parse_args().k_neg)
            if not negs: continue
            all_rows.append({
                "query": q,
                "positive": it["ce_text"],
                "negatives": negs,
                "meta": {
                    "name": it["name"],
                    "region": it["region"], "mood": it["mood"], "type": it["type"],
                    "veg": it["veg"], "texture": it["texture"],
                    "price": it["price"], "unit": it["unit"],
                    "price_bucket": it.get("price_bucket",""),
                    "time_bucket": it.get("time_bucket",""),
                    "time": it["time"], "image": it["image"],
                    "desc": it["desc"], "ingredients": it["ingredients"],
                    "nutrition": it["nutrition"],
                    "retrieval_text": it["retrieval_text"],
                    "ce_text": it["ce_text"]
                }
            })

    random.shuffle(all_rows)

    # stratified-ish split theo (Region,Type,Veg)
    def gkey(m):
        return f"R:{(m.get('region') or 'unknown').lower()}|T:{(m.get('type') or 'unknown').lower()}|V:{(m.get('veg') or 'unknown').lower()}"
    groups = defaultdict(list)
    for r in all_rows:
        groups[gkey(r["meta"])].append(r)

    dev_rows, train_rows = [], []
    n_dev_ratio = parse_args().dev_ratio
    for _, lst in groups.items():
        random.shuffle(lst)
        n = max(1, int(round(len(lst) * n_dev_ratio)))
        dev_rows.extend(lst[:n])
        train_rows.extend(lst[n:])

    # save
    out_train = Path(parse_args().out_train)
    out_dev   = Path(parse_args().out_dev)
    with out_train.open("w", encoding="utf-8") as f:
        for r in train_rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out_dev.open("w", encoding="utf-8") as f:
        for r in dev_rows:   f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Saved train: {out_train} | rows={len(train_rows)}")
    print(f"✅ Saved dev  : {out_dev}   | rows={len(dev_rows)}")

if __name__ == "__main__":
    main()
