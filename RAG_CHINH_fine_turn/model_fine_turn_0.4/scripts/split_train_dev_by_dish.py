# scripts/split_train_dev_by_dish.py
import json, random
from pathlib import Path
random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
INP  = ROOT / "data" / "pairs_attribute.jsonl"
OUT_DIR = ROOT / "data"
TRAIN = OUT_DIR / "pairs_attribute_train.jsonl"
DEV   = OUT_DIR / "pairs_attribute_dev.jsonl"

assert INP.exists(), f"❌ Không thấy {INP}"

# Gom theo món
by_name = {}
with open(INP, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        name = r.get("meta",{}).get("name","__NA__")
        by_name.setdefault(name, []).append(r)

names = list(by_name.keys())
random.shuffle(names)
# 80/20 theo MÓN
split_idx = int(0.8 * len(names))
train_names = set(names[:split_idx])
dev_names   = set(names[split_idx:])

def dump(path, name_set):
    cnt_rows, cnt_names = 0, set()
    with open(path, "w", encoding="utf-8") as f:
        for n in name_set:
            for r in by_name[n]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                cnt_rows += 1
            cnt_names.add(n)
    return cnt_rows, len(cnt_names)

tr_rows, tr_names = dump(TRAIN, train_names)
dv_rows, dv_names = dump(DEV, dev_names)

print(f"✅ Train: rows={tr_rows}, unique_món={tr_names} -> {TRAIN}")
print(f"✅ Dev  : rows={dv_rows}, unique_món={dv_names} -> {DEV}")
