# Day 8 — RAG Pipeline

## Tổng quan

Chatbot RAG tiếng Việt trả lời câu hỏi về quy chế đào tạo, học phí, học bổng và dịch vụ sinh viên. Pipeline hỗ trợ dense retrieval, BM25Plus, Reciprocal Rank Fusion (RRF), PageIndex fallback, citation và giao diện Streamlit.

Hệ thống chạy được ở chế độ offline bằng embedding cục bộ và câu trả lời trích xuất có citation. Khi cấu hình API key, phần generation có thể dùng OpenAI, Gemini hoặc Anthropic.

## Trạng thái hoàn thành

- 3 PDF chính sách và 5 bài viết web, đã chuẩn hóa thành Markdown.
- 8 tài liệu, 442 chunk được đồng bộ trong ChromaDB bằng ID ổn định.
- Dense + BM25Plus → RRF; fallback PageIndex dùng cosine score gốc.
- Generation có kiểm tra citation và safe refusal cho câu hỏi ngoài miền/lỗi provider.
- Streamlit hiển thị câu trả lời, nguồn, retrieval method và score.
- Golden dataset 17 câu, 4 proxy metric và so sánh A/B có thể chạy lại.
- Toàn bộ 24 contract/acceptance/robustness test đang pass.

## Quick start

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
# macOS/Linux: cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
```

API key LLM là tùy chọn. Nếu không có key, ứng dụng dùng generator trích xuất cục bộ. Không commit `.env`.

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py

# 4. Chạy lại đánh giá A/B
python -m group_project.evaluation.evaluate
```

## Kiến trúc

```text
PDF/DOCX + web JSON → Markdown → chunk → embedding → ChromaDB
                                           ├─ dense search ─┐
                                           └─ BM25Plus ─────┴─ RRF
                                                             ├─ đủ tin cậy → generation + citation
                                                             └─ điểm dense thấp → PageIndex fallback
```

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 cùng trả về `SearchResult` theo một schema.
- RRF chỉ gộp thứ hạng một lần; fallback dùng cosine score gốc của dense retrieval.
- Index xóa ID cũ trước khi upsert, nên chạy lại không để lại chunk lỗi thời.
- Mặc định `SCORE_THRESHOLD=0.3`; cần hiệu chỉnh thêm nếu thay corpus/model.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Evaluation result](group_project/evaluation/RESULT.md): kết quả và phân tích A/B.
- [Individual report](reports/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```
