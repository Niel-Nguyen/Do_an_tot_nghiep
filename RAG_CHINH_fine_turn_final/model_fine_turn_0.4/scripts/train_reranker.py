# -*- coding: utf-8 -*-
# scripts/train_reranker.py
import os, json, random, logging, math, argparse
from statistics import mean
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np
import torch
from sentence_transformers import CrossEncoder, InputExample, LoggingHandler
from torch.utils.data import DataLoader

# Seeds & env
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ===== CLI =====
parser = argparse.ArgumentParser()
parser.add_argument("--base_model", type=str,
    default=os.environ.get("CE_BASE_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
    help="VD: cross-encoder/ms-marco-MiniLM-L-12-v2")
parser.add_argument("--batch_size", type=int, default=int(os.environ.get("CE_BATCH", 16)))
parser.add_argument("--epochs", type=int, default=8)
parser.add_argument("--lr", type=float, default=2e-5)
parser.add_argument("--max_len", type=int, default=224)
parser.add_argument("--eval_batch_size", type=int, default=64)
parser.add_argument("--patience", type=int, default=2)
args = parser.parse_args()

# ===== Logging =====
logging.basicConfig(format='%(asctime)s - %(message)s',
                    level=logging.INFO,
                    handlers=[LoggingHandler()])

# ===== Paths =====
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
TRAIN_PATH = DATA_DIR / "pairs_attribute_train.jsonl"
DEV_PATH   = DATA_DIR / "pairs_attribute_dev.jsonl"
OUT_DIR    = ROOT / "model" / "reranker_food_attr"
BASE_MODEL = args.base_model

print("TRAIN_PATH =", TRAIN_PATH.resolve())
print("DEV_PATH   =", DEV_PATH.resolve())
print("BASE_MODEL =", BASE_MODEL)

assert TRAIN_PATH.exists(), "⚠️ Không tìm thấy train set"
assert DEV_PATH.exists(),   "⚠️ Không tìm thấy dev set"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== Hyperparams =====
BATCH_SIZE        = args.batch_size
MAX_LEN           = args.max_len
EPOCHS            = args.epochs
LR                = args.lr
WARMUP_STEPS      = 100
PATIENCE          = args.patience
POS_REPEAT        = 4
EVAL_BATCH_SIZE   = args.eval_batch_size

# ===== Dataset utils =====
def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

def load_examples(path):
    rows = load_jsonl(path)
    data = []
    for r in rows:
        q = r["query"]
        pos_text = r.get("positive") or r.get("meta", {}).get("ce_text","")
        if not pos_text:
            continue
        for _ in range(POS_REPEAT):
            data.append(InputExample(texts=[q, pos_text], label=1.0))
        for neg_text in r.get("negatives", []):
            data.append(InputExample(texts=[q, neg_text], label=0.0))
    return data

train_data = load_examples(TRAIN_PATH)
train_loader = DataLoader(
    train_data,
    batch_size=BATCH_SIZE, shuffle=True, drop_last=False,
    pin_memory=False, num_workers=0
)

# ===== Init model =====
model = CrossEncoder(BASE_MODEL, num_labels=1, max_length=MAX_LEN)
device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Use pytorch device: {device}")

# ===== Evaluators =====
def compute_random_baseline(jsonl_path):
    rows = load_jsonl(jsonl_path)
    if not rows:
        return 0.0
    k_negs = [len(r.get("negatives", [])) for r in rows]
    avg_k = mean(k_negs) if k_negs else 0
    total = 1.0 + avg_k
    return 1.0 / total if total > 0 else 0.0

def _rank_blocks(rows, scores):
    ranks, pos_scores = [], []
    ptr = 0
    for r in rows:
        cands = 1 + len(r.get("negatives", []))
        s = scores[ptr:ptr+cands]
        ptr += cands
        ord_idx = list(sorted(range(cands), key=lambda i: float(s[i]), reverse=True))
        rank = ord_idx.index(0) + 1
        ranks.append(rank)
        pos_scores.append(float(s[0]))
    return ranks, pos_scores

def eval_metrics(jsonl_path, model, k=10, batch_size=EVAL_BATCH_SIZE):
    rows = load_jsonl(jsonl_path)
    if not rows:
        return 0.0, 0.0, 0.0

    all_pairs = []
    for r in rows:
        q = r["query"]
        pos = r.get("positive") or r.get("meta", {}).get("ce_text","")
        cands = [pos] + r.get("negatives", [])
        all_pairs.extend([[q, c] for c in cands])

    scores = model.predict(
        all_pairs,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    ranks, _ = _rank_blocks(rows, scores)
    total = len(rows)
    hit1 = sum(1 for rk in ranks if rk == 1) / total
    mrr  = sum(1.0/rk for rk in ranks) / total
    ndcg = sum((1.0 / math.log2(rk + 1)) if rk <= k else 0.0 for rk in ranks) / total
    return hit1, mrr, ndcg

def eval_metrics_detailed(jsonl_path, model, ks=(1,3), batch_size=EVAL_BATCH_SIZE):
    rows = load_jsonl(jsonl_path)
    if not rows:
        return {}

    all_pairs = []
    for r in rows:
        q = r["query"]
        pos = r.get("positive") or r.get("meta", {}).get("ce_text","")
        cands = [pos] + r.get("negatives", [])
        all_pairs.extend([[q, c] for c in cands])

    scores = model.predict(
        all_pairs,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    ranks, pos_scores = _rank_blocks(rows, scores)

    def key_from_meta(m):
        reg = (m.get("region") or "unknown").strip().lower()
        typ = (m.get("type") or "unknown").strip().lower()
        veg = (m.get("veg") or "unknown").strip().lower()
        return reg, typ, veg

    buckets = {
        "global": defaultdict(float),
        "region": defaultdict(lambda: defaultdict(float)),
        "type": defaultdict(lambda: defaultdict(float)),
        "veg": defaultdict(lambda: defaultdict(float)),
    }
    count_global = 0
    count_region = Counter()
    count_type   = Counter()
    count_veg    = Counter()

    for r, rk, sc in zip(rows, ranks, pos_scores):
        m = r.get("meta", {})
        reg, typ, veg = key_from_meta(m)
        count_global += 1
        buckets["global"]["mrr"] += 1.0 / rk
        for K in ks:
            if rk <= K:
                buckets["global"][f"hit@{K}"] += 1
                buckets["global"][f"ndcg@{K}"] += (1.0 / math.log2(rk + 1))

        count_region[reg] += 1
        buckets["region"][reg]["mrr"] += 1.0 / rk
        for K in ks:
            if rk <= K:
                buckets["region"][reg][f"hit@{K}"] += 1
                buckets["region"][reg][f"ndcg@{K}"] += (1.0 / math.log2(rk + 1))

        count_type[typ] += 1
        buckets["type"][typ]["mrr"] += 1.0 / rk
        for K in ks:
            if rk <= K:
                buckets["type"][typ][f"hit@{K}"] += 1
                buckets["type"][typ][f"ndcg@{K}"] += (1.0 / math.log2(rk + 1))

        count_veg[veg] += 1
        buckets["veg"][veg]["mrr"] += 1.0 / rk
        for K in ks:
            if rk <= K:
                buckets["veg"][veg][f"hit@{K}"] += 1
                buckets["veg"][veg][f"ndcg@{K}"] += (1.0 / math.log2(rk + 1))

    out = {"global": {}, "region": {}, "type": {}, "veg": {}}
    if count_global > 0:
        out["global"]["mrr"] = buckets["global"]["mrr"]/count_global
        for K in ks:
            out["global"][f"hit@{K}"]  = buckets["global"].get(f"hit@{K}",0.0)/count_global
            out["global"][f"ndcg@{K}"] = buckets["global"].get(f"ndcg@{K}",0.0)/count_global

    for k, cnt in count_region.items():
        if cnt == 0: continue
        d = buckets["region"][k]
        row = {"count": cnt, "mrr": d["mrr"]/cnt}
        for K in ks:
            row[f"hit@{K}"]  = d.get(f"hit@{K}",0.0)/cnt
            row[f"ndcg@{K}"] = d.get(f"ndcg@{K}",0.0)/cnt
        out["region"][k] = row

    for k, cnt in count_type.items():
        if cnt == 0: continue
        d = buckets["type"][k]
        row = {"count": cnt, "mrr": d["mrr"]/cnt}
        for K in ks:
            row[f"hit@{K}"]  = d.get(f"hit@{K}",0.0)/cnt
            row[f"ndcg@{K}"] = d.get(f"ndcg@{K}",0.0)/cnt
        out["type"][k] = row

    for k, cnt in count_veg.items():
        if cnt == 0: continue
        d = buckets["veg"][k]
        row = {"count": cnt, "mrr": d["mrr"]/cnt}
        for K in ks:
            row[f"hit@{K}"]  = d.get(f"hit@{K}",0.0)/cnt
            row[f"ndcg@{K}"] = d.get(f"ndcg@{K}",0.0)/cnt
        out["veg"][k] = row

    return out

rand_base = compute_random_baseline(DEV_PATH)
print(f"[Baseline ngẫu nhiên] Hit@1 ≈ {rand_base:.3f}")

# ===== Training with early stopping =====
best_mrr = -1.0
no_improve = 0
best_dir = OUT_DIR / "best"
best_dir.mkdir(parents=True, exist_ok=True)

for ep in range(1, EPOCHS+1):
    logging.info(f"==== Epoch {ep}/{EPOCHS} ====")
    model.fit(
        train_dataloader=train_loader,
        epochs=1,
        warmup_steps=WARMUP_STEPS if ep == 1 else 0,
        output_path=None,
        show_progress_bar=True,
        optimizer_params={'lr': LR}
    )
    hit1, mrr, ndcg = eval_metrics(DEV_PATH, model, k=10)
    logging.info(f"[DEV] Hit@1={hit1:.4f} | MRR@10={mrr:.4f} | NDCG@10={ndcg:.4f} | Lift vs rnd={hit1 - rand_base:+.4f}")

    detail = eval_metrics_detailed(DEV_PATH, model, ks=(1,3))
    if detail:
        g = detail["global"]
        logging.info(f"[DEV][GLOBAL] Hit@1={g.get('hit@1',0):.4f} | Hit@3={g.get('hit@3',0):.4f} | MRR={g.get('mrr',0):.4f} | NDCG@3={g.get('ndcg@3',0):.4f}")
        weak_regions = sorted(detail["region"].items(), key=lambda x: (x[1]["hit@1"], x[1]["count"]))
        weak_types   = sorted(detail["type"].items(),   key=lambda x: (x[1]["hit@1"], x[1]["count"]))
        weak_vegs    = sorted(detail["veg"].items(),    key=lambda x: (x[1]["hit@1"], x[1]["count"]))
        logging.info(f"[DEV][WEAK] Region(top-3): {weak_regions[:3]}")
        logging.info(f"[DEV][WEAK] Type  (top-3): {weak_types[:3]}")
        logging.info(f"[DEV][WEAK] Veg   (top-3): {weak_vegs[:3]}")

    if mrr > best_mrr + 1e-4:
        best_mrr = mrr
        no_improve = 0
        model.save(str(best_dir))
        logging.info(f"✅ Improved. Saved BEST to: {best_dir}")
    else:
        no_improve += 1
        logging.info(f"⚠️ No improvement ({no_improve}/{PATIENCE})")
        if no_improve >= PATIENCE:
            logging.info("⛔ Early stopping triggered.")
            break

# Save last
model.save(str(OUT_DIR))
logging.info(f"🟢 Saved LAST to: {OUT_DIR}")

# Final metrics for BEST and LAST
try:
    best_model = CrossEncoder(str(best_dir), num_labels=1, max_length=MAX_LEN)
    b_hit1, b_mrr, b_ndcg = eval_metrics(DEV_PATH, best_model, k=10)
    logging.info(f"[BEST] DEV Hit@1={b_hit1:.4f} | MRR@10={b_mrr:.4f} | NDCG@10={b_ndcg:.4f} | Lift vs rnd={b_hit1 - rand_base:+.4f}")

    b_detail = eval_metrics_detailed(DEV_PATH, best_model, ks=(1,3))
    if b_detail:
        g = b_detail["global"]
        logging.info(f"[BEST][GLOBAL] Hit@1={g.get('hit@1',0):.4f} | Hit@3={g.get('hit@3',0):.4f} | MRR={g.get('mrr',0):.4f} | NDCG@3={g.get('ndcg@3',0):.4f}")
except Exception as e:
    logging.warning(f"Không load được BEST: {e}")

l_hit1, l_mrr, l_ndcg = eval_metrics(DEV_PATH, model, k=10)
logging.info(f"[LAST] DEV Hit@1={l_hit1:.4f} | MRR@10={l_mrr:.4f} | NDCG@10={l_ndcg:.4f} | Lift vs rnd={l_hit1 - rand_base:+.4f}")

l_detail = eval_metrics_detailed(DEV_PATH, model, ks=(1,3))
if l_detail:
    g = l_detail["global"]
    logging.info(f"[LAST][GLOBAL] Hit@1={g.get('hit@1',0):.4f} | Hit@3={g.get('hit@3',0):.4f} | MRR={g.get('mrr',0):.4f} | NDCG@3={g.get('ndcg@3',0):.4f}")

print("✅ Done.")
# === Save evaluation report for grading ===
report_path_best = OUT_DIR / "best_eval.json"
report_path_last = OUT_DIR / "last_eval.json"

try:
    json.dump(b_detail or {}, open(report_path_best, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
except:
    pass
try:
    json.dump(l_detail or {}, open(report_path_last, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
except:
    pass

print(f"📄 Saved eval reports to:\n - {report_path_best}\n - {report_path_last}")
