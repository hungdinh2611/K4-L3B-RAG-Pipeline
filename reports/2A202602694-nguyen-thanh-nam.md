# Individual contribution report — Nguyễn Thành Nam

## Thông tin

- Họ và tên: Nguyễn Thành Nam
- Mã học viên: 2A202602694
- Nhóm: K4-L3B
- Repository/branch: `K4-L3B-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc trực tiếp làm | File/commit | Trạng thái |
|---|---|---|---|
| Retrieval pipeline | Tích hợp dense, BM25, RRF và PageIndex fallback | `src/task7_reranking.py`–`src/task9_retrieval_pipeline.py`, `ae27f50` | Done |
| Generation/UI | Generation có citation, safe refusal và chatbot Streamlit | `src/task10_generation.py`, `app.py`, `ae27f50` | Done |
| Evaluation | Golden dataset 17 câu, A/B dense-only với hybrid + RRF, báo cáo metrics | `group_project/evaluation/`, `ae27f50` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng RRF để hợp nhất thứ hạng dense và BM25 đúng một lần.  
   **Lý do/evidence:** Cosine similarity và BM25 có thang điểm khác nhau; RRF tránh cộng trực tiếp hai score.  
   **Trade-off:** RRF không học trọng số và có thể đưa chunk nhiễu vào top-k.

2. **Quyết định:** Có generator trích xuất offline kèm kiểm tra ID citation.  
   **Lý do/evidence:** Demo vẫn chạy khi không có API key và từ chối an toàn với câu ngoài miền.  
   **Trade-off:** Câu trả lời ít tự nhiên hơn LLM và phụ thuộc chất lượng đoạn trích.

## Kiểm thử và kết quả

- Toàn bộ contract, acceptance và robustness test: 24 test pass.
- Streamlit AppTest chạy thành công với truy vấn có citation.
- Hybrid + RRF đạt trung bình proxy 0,8724, cao hơn dense-only 0,1161 trên 17 câu golden.

## Điều còn hạn chế

- Bốn metric hiện là proxy offline, chưa phải RAGAS hoặc human evaluation.
- Nếu có thêm thời gian, hiệu chỉnh fallback bằng tập câu hỏi ngoài miền lớn hơn và đo với LLM judge.

## Xác nhận đóng góp

Báo cáo này được lập từ lịch sử commit `ae27f50`; thành viên cần xác nhận trước khi nộp.

- Ngày: 2026-09-25
- Tên thành viên: Nguyễn Thành Nam
