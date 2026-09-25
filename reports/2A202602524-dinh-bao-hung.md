# Individual contribution report — Đinh Bảo Hưng

## Thông tin

- Họ và tên: Đinh Bảo Hưng
- Mã học viên: 2A202602524
- Nhóm: K4-L3B
- Repository/branch: `K4-L3B-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc trực tiếp làm | File/commit | Trạng thái |
|---|---|---|---|
| Data | Thu thập 3 PDF chính sách, crawl 5 bài viết và chuẩn hóa Markdown | `src/task1_collect_legal_docs.py`–`src/task3_convert_markdown.py`, `f9a5c2e` | Done |
| Indexing | Recursive chunking, embedding cục bộ và lưu ChromaDB | `src/task4_chunking_indexing.py`, `6cd619d` | Done |
| Retrieval | Dense search và BM25 trên cùng corpus chunk | `src/task5_semantic_search.py`, `src/task6_lexical_search.py`, `6cd619d` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng recursive chunking với ID ổn định theo tài liệu và chỉ số chunk.  
   **Lý do/evidence:** Giữ được metadata nguồn xuyên suốt và cho phép upsert lại ChromaDB.  
   **Trade-off:** Chunk cố định chưa tối ưu riêng cho bảng và cấu trúc điều khoản dài.

2. **Quyết định:** Dense retrieval và BM25 dùng chung tập chunk.  
   **Lý do/evidence:** Hai nhánh có thể ghép bằng ID trong RRF mà không làm mất nguồn.  
   **Trade-off:** BM25 tokenization đơn giản chưa tách từ tiếng Việt chuyên sâu.

## Kiểm thử và kết quả

- Corpus hiện có 8 tài liệu, tạo 442 chunk và ChromaDB có đúng 442 bản ghi.
- Toàn bộ contract, acceptance và robustness test: 24 test pass.
- Chạy lại index không tạo ID trùng và loại chunk cũ không còn trong corpus.

## Điều còn hạn chế

- Dữ liệu web còn một số menu/liên kết phụ; nên bổ sung bước làm sạch theo cấu trúc trang.
- Nếu có thêm thời gian, thử semantic chunking và so sánh retrieval metrics với recursive chunking.

## Xác nhận đóng góp

Báo cáo này được lập từ lịch sử commit `f9a5c2e` và `6cd619d`; thành viên cần xác nhận trước khi nộp.

- Ngày: 2026-09-25
- Tên thành viên: Đinh Bảo Hưng
