# core/tesst.py
# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# ==== Ensure project root on sys.path (để import core.*, models.*) ====
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]  # .../RAG_CHINH_full_topping
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==== (Tùy chọn) chỉ định thư mục model fine-tune nếu bạn để vị trí khác ====
DEFAULT_RERANKER_DIR = PROJECT_ROOT / "model_fine_turn_0.4" / "model" / "reranker_food_attr" / "best"
os.environ.setdefault("FOOD_RERANKER_DIR", str(DEFAULT_RERANKER_DIR))
os.environ.setdefault("FOOD_RERANKER_MAX_LEN", "224")

# ==== Imports sau khi đã thêm sys.path ====
from core.rag_system import rag_system
from models.ai_models import ai_models
from models.data_models import VietnameseDish
from config.settings import settings

# (Optional) load Excel seed
def try_load_excel(path: str) -> List[VietnameseDish]:
    """
    Đọc Excel và chuẩn hóa 1 số trường số (calories/fat/sugar/protein/cook_time/price) về int nếu có thể.
    """
    try:
        from utils.excel_loader import load_dishes_from_excel
        dishes = load_dishes_from_excel(path)

        # Chuẩn hóa kiểu dữ liệu (an toàn cho filter số)
        def _to_int(x):
            try:
                return int(str(x).replace(".", "").replace(",", "").strip())
            except Exception:
                return x

        for d in dishes:
            # những field này thường là số
            if hasattr(d, "calories"):
                d.calories = _to_int(getattr(d, "calories", None))
            if hasattr(d, "fat"):
                d.fat = _to_int(getattr(d, "fat", None))
            if hasattr(d, "fiber"):
                d.fiber = _to_int(getattr(d, "fiber", None))
            if hasattr(d, "sugar"):
                d.sugar = _to_int(getattr(d, "sugar", None))
            if hasattr(d, "protein"):
                d.protein = _to_int(getattr(d, "protein", None))
            if hasattr(d, "cook_time"):
                d.cook_time = _to_int(getattr(d, "cook_time", None))
            if hasattr(d, "price"):
                d.price = _to_int(getattr(d, "price", None))

        if dishes:
            print(f"[INFO] Loaded {len(dishes)} dishes from Excel: {path}")
            return dishes
    except Exception as e:
        print(f"[WARN] Cannot load Excel '{path}': {e}")
    return []

def ensure_models():
    print(f"[INFO] Project root: {PROJECT_ROOT}")
    print(f"[INFO] FOOD_RERANKER_DIR = {os.environ.get('FOOD_RERANKER_DIR')}")
    ok = ai_models.initialize_models()
    if not ok:
        raise RuntimeError("Không khởi tạo được ai_models (LLM / embeddings / vectorstore).")

def init_rag(dishes: List[VietnameseDish]):
    ok = rag_system.initialize(dishes)
    if not ok:
        raise RuntimeError("RAG initialize failed. Kiểm tra lại ai_models & cấu hình.")
    # kích hoạt lazy reranker
    _ = rag_system.search_relevant_dishes("ping reranker")

def pretty_print_results(q: str, k_print: int = 5):
    res = rag_system.search_relevant_dishes(q)
    stats = rag_system.get_statistics()
    reranker_loaded = stats["search_config"].get("reranker_loaded")
    print(f"Reranker loaded? -> {reranker_loaded}")
    if not res:
        print("[WARN] Không có kết quả. Hãy kiểm tra embeddings, retriever hoặc dữ liệu.")
        return
    for r in res[:k_print]:
        print(f"- {r.dish.name} | score={getattr(r, 'score', None)} | reason={getattr(r, 'relevance','')}")
    print("\n===== CONTEXT =====")
    print(rag_system.get_context_for_llm(q))

def _strict_template_from_results(results) -> str:
    """Sinh context ngắn gọn, chỉ gồm các món hợp lệ (từ RAG)."""
    lines = []
    for i, r in enumerate(results, 1):
        d = r.dish
        desc = (d.description or "").strip()
        if len(desc) > 160:
            desc = desc[:160] + "..."
        lines.append(
            f"{i}. {d.name} — vùng: {d.region or 'N/A'}; tính chất: {getattr(d, 'texture','') or 'N/A'}; "
            f"loại: {getattr(d, 'dish_type','') or 'N/A'}; thời gian: {getattr(d, 'cook_time','') or 'N/A'}; "
            f"giá: {getattr(d, 'price','') or 'N/A'}; mô tả: {desc}"
        )
    return "\n".join(lines)

def answer_with_llm_free(query: str):
    """Chế độ tự do (có thể bịa) – giữ lại để so sánh."""
    ctx = rag_system.get_context_for_llm(query)
    llm = ai_models.get_llm()

    system_msg = (
        "Bạn là trợ lý nhà hàng Việt, trả lời ngắn gọn, chính xác. "
        "Chỉ dựa trên NGỮ CẢNH cung cấp; nếu thiếu thông tin thì nói chưa rõ, không bịa."
    )
    user_msg = (
        f"Câu hỏi: {query}\n\n"
        f"NGỮ CẢNH (từ RAG):\n{ctx}\n\n"
        "Hãy trả lời bằng tiếng Việt, liệt kê món phù hợp (nếu có) và giải thích ngắn gọn."
    )

    try:
        result = llm.invoke([("system", system_msg), ("human", user_msg)])
        text = getattr(result, "content", None) or str(result)
    except Exception as e:
        text = f"[LLM ERROR] {e}"

    print("\n===== LLM ANSWER (FREE) =====")
    print(text)
    print("==================================\n")

def answer_with_llm_strict(query: str, top_k: int = 5):
    """
    Chế độ STRICT:
    - Lấy top-k món từ RAG.
    - Bắt LLM chỉ được chọn trong danh sách cho phép (allowed_names).
    - Yêu cầu output JSON có cấu trúc, rồi hậu kiểm.
    - Nếu không còn món hợp lệ => fallback in thẳng top-k từ RAG, KHÔNG bịa.
    """
    results = rag_system.search_relevant_dishes(query)
    if not results:
        print("\n===== STRICT ANSWER =====")
        print("Không tìm thấy món phù hợp trong dữ liệu. Vui lòng hỏi khác hoặc kiểm tra data.")
        print("==================================\n")
        return

    results = results[:top_k]
    allowed_names = [r.dish.name for r in results]

    compact_ctx = _strict_template_from_results(results)
    llm = ai_models.get_llm()

    system_msg = (
        "Bạn là trợ lý nhà hàng Việt. TUYỆT ĐỐI không được nêu món ngoài danh sách cho phép. "
        "Chỉ được chọn từ 'allowed_names'. Nếu không phù hợp, trả về mảng rỗng."
    )
    user_msg = (
        "Nhiệm vụ: Chọn 1-5 món phù hợp nhất cho câu hỏi phía dưới, "
        "NHƯNG chỉ được chọn từ allowed_names.\n\n"
        f"Câu hỏi: {query}\n\n"
        "NGỮ CẢNH rút gọn (RAG top-k):\n"
        f"{compact_ctx}\n\n"
        f"allowed_names = {json.dumps(allowed_names, ensure_ascii=False)}\n\n"
        "Hãy trả lời đúng **định dạng JSON** sau (KHÔNG thêm chữ, KHÔNG markdown):\n"
        '{\n'
        '  "picks": [\n'
        '    {"name": "<tên món trong allowed_names>", "why": "<lý do ngắn gọn>"}\n'
        '  ]\n'
        '}\n'
        "Nếu không có món nào phù hợp, trả về: {\"picks\": []}"
    )

    raw_text = ""
    try:
        result = llm.invoke([("system", system_msg), ("human", user_msg)])
        raw_text = getattr(result, "content", None) or str(result)
    except Exception as e:
        raw_text = f'{{"error":"LLM ERROR: {e}"}}'

    valid_picks: List[Dict[str, Any]] = []
    try:
        data = json.loads(raw_text)
        for item in data.get("picks", []):
            name = (item.get("name") or "").strip()
            why = (item.get("why") or "").strip()
            if name in allowed_names:
                valid_picks.append({"name": name, "why": why})
    except Exception:
        valid_picks = []

    print("\n===== LLM ANSWER (STRICT) =====")
    if valid_picks:
        for i, p in enumerate(valid_picks, 1):
            print(f"{i}. {p['name']} — {p['why']}")
    else:
        print("Không nhận được lựa chọn hợp lệ từ LLM, hiển thị gợi ý từ RAG (an toàn):")
        for i, r in enumerate(results, 1):
            d = r.dish
            reason_hint = (d.description or "").strip()
            if len(reason_hint) > 120:
                reason_hint = reason_hint[:120] + "..."
            print(f"{i}. {d.name} — phù hợp vì gần truy vấn; {reason_hint}")
    print("==================================\n")

def run_repl(mode: str):
    print("\n🧪 REPL test — gõ câu hỏi trực tiếp hoặc dùng lệnh:")
    print("  :ask <câu hỏi>     → RAG + LLM (theo mode bạn chọn)")
    print("  :search <câu hỏi>  → Chỉ tìm kiếm & hiển thị top kết quả + context")
    print("  :ctx <câu hỏi>     → In riêng NGỮ CẢNH (context) từ RAG")
    print("  :stats             → In thống kê RAG")
    print("  :exit              → Thoát\n")

    while True:
        try:
            q = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not q:
            continue
        if q.lower() in (":exit", ":quit"):
            print("Bye!")
            break
        if q.lower().startswith(":stats"):
            print(rag_system.get_statistics())
            continue
        if q.lower().startswith(":ctx"):
            rest = q[len(":ctx"):].strip()
            if not rest:
                print("Cú pháp: :ctx <câu hỏi>")
            else:
                print("\n===== CONTEXT =====")
                print(rag_system.get_context_for_llm(rest))
                print("===================\n")
            continue
        if q.lower().startswith(":search"):
            rest = q[len(":search"):].strip()
            if not rest:
                print("Cú pháp: :search <câu hỏi>")
            else:
                pretty_print_results(rest)
            continue
        if q.lower().startswith(":ask"):
            rest = q[len(":ask"):].strip()
            if not rest:
                print("Cú pháp: :ask <câu hỏi>")
            else:
                if mode == "strict":
                    answer_with_llm_strict(rest)
                else:
                    answer_with_llm_free(rest)
            continue

        if mode == "strict":
            answer_with_llm_strict(q)
        else:
            answer_with_llm_free(q)

def main():
    parser = argparse.ArgumentParser(description="Tester cho RAG & RAG+LLM (STRICT mặc định)")
    parser.add_argument("--excel", type=str, default="", help="Đường dẫn file Excel (data100mon.xlsx)")
    parser.add_argument("--ask", type=str, default="", help="Hỏi một câu rồi thoát (RAG+LLM)")
    parser.add_argument("--search", type=str, default="", help="Chỉ tìm kiếm & in context rồi thoát")
    parser.add_argument("--mode", type=str, choices=["strict", "free"], default="strict",
                        help="strict: chỉ chọn trong top-k từ RAG; free: để LLM tự do")
    parser.add_argument("--topk", type=int, default=5, help="Số ứng viên RAG chuyển cho LLM (strict)")
    args = parser.parse_args()

    ensure_models()

    # ==== Nạp dữ liệu Excel thật ====
    excel_path = (
        args.excel.strip()
        or settings.DATA_FILE_PATH
        or str(PROJECT_ROOT / "data100mon.xlsx")
    )
    dishes: List[VietnameseDish] = try_load_excel(excel_path)
    if not dishes:
        raise SystemExit(
            f"[FATAL] Không đọc được dữ liệu từ Excel. "
            f"Thử chạy lại với --excel <đường_dẫn_tới_data100mon.xlsx>. "
            f"Đang dùng: {excel_path}"
        )

    init_rag(dishes)

    # One-shot modes
    if args.ask:
        if args.mode == "strict":
            answer_with_llm_strict(args.ask, top_k=args.topk)
        else:
            answer_with_llm_free(args.ask)
        return
    if args.search:
        pretty_print_results(args.search)
        return

    # REPL
    run_repl(args.mode)

if __name__ == "__main__":
    main()
