RERANKER – Fine-tune Cross-Encoder for Food RAG (Vietnamese)

Files generated:
- /mnt/data/corpus.jsonl          : Mỗi món 1 passage đã chuẩn hoá
- /mnt/data/pairs.jsonl           : ~1200 cặp (query, positive, negatives) để train Reranker
- /mnt/data/eval_queries.jsonl    : ~80 query để đánh giá trước/sau
- /mnt/data/02_train_reranker.ipynb : Notebook huấn luyện (chạy trên Colab/GPU khuyến nghị)
- /mnt/data/03_eval_reranker.ipynb  : Notebook đánh giá MRR@10, Recall@10
- /mnt/data/reranker_service.py     : Service Python để tích hợp vào Flask/RAG

Cách dùng nhanh:
1) Huấn luyện:
   - Mở 02_train_reranker.ipynb trên Colab/Jupyter và chạy toàn bộ cell.
   - Model sẽ được lưu tại /mnt/data/reranker_food

2) Đánh giá:
   - Mở 03_eval_reranker.ipynb, sửa đường dẫn model nếu cần, chạy để lấy MRR@10/Recall@10.

3) Tích hợp vào app (pseudo):
   from reranker_service import RerankerService
   reranker = RerankerService(model_path="path/to/reranker_food", enabled=True)

   def retrieve_with_rerank(query, candidates):
       # candidates: list[str] hoặc list[{'text': '...'}]
       return reranker.rerank(query, candidates, top_n=3)

4) A/B test:
   - Cho phép query param ?rerank=1 để bật reranker trong API.
   - Ghi log top contexts để so sánh trước/sau.

Ghi chú:
- Price trong corpus là 'k' (nghìn VND). Ví dụ 120k.
- Bạn có thể tăng/giảm số lượng cặp bằng cách chỉnh tham số augmentation trong script.
