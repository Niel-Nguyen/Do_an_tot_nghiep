# scripts/test_reranker_manual.py

from sentence_transformers import CrossEncoder
from pathlib import Path

# ==== Load model đã fine-tune ====
MODEL_PATH = Path("model_fine_turn/model/reranker_food_attr")
model = CrossEncoder(
    model_name_or_path=MODEL_PATH.as_posix(),
    local_files_only=True
)

# ==== Danh sách món ăn để test (bạn có thể sửa tùy ý) ====
dishes = [
    "Phở bò Hà Nội, giá dưới 50K, hợp tâm trạng nhớ nhà",
    "Cơm gà xối mỡ, miền Nam, hợp ngày bận rộn",
    "Bún chả Hà Nội, món truyền thống miền Bắc",
    "Lẩu Thái chua cay, hợp ngày mưa buồn",
    "Cơm tấm sườn bì chả, giá rẻ, hợp dân văn phòng"
]

while True:
    query = input("\n📝 Nhập câu hỏi (hoặc gõ 'exit' để thoát): ")
    if query.lower().strip() == "exit":
        break

    pairs = [(query, d) for d in dishes]
    scores = model.predict(pairs)

    ranked = sorted(zip(dishes, scores), key=lambda x: x[1], reverse=True)

    print("\n🏆 Top món ăn phù hợp:")
    for i, (dish, score) in enumerate(ranked, 1):
        print(f"{i}. {dish} (score={score:.4f})")
