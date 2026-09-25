# Kết quả đánh giá RAG

## Run information

| Trường | Giá trị |
| --- | --- |
| Ngày chạy | 2026-09-25 |
| Framework | `group_project/evaluation/evaluate.py` (đánh giá offline) |
| Evaluator | Quy tắc đối chiếu nguồn và từ khóa; không sử dụng LLM judge |
| Generator | Trích nguyên văn từ chunk có citation; khi không có API key, dò thêm trong các file nguồn đã được truy xuất |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Corpus | 8 tài liệu, 442 chunk; commit nền `f9a5c2e` cùng dữ liệu làm việc hiện tại |
| Golden dataset | 17 câu hỏi có đáp án, context và tên nguồn |
| `top_k` | 5 |
| Fallback threshold | Không áp dụng cho so sánh A/B (`score_threshold=-1`); mặc định demo 0,3, chưa hiệu chỉnh trên tập ngoài miền đủ lớn |

## Configurations

- **Config A — dense-only:** Chroma cosine, cùng embedding và `top_k=5`.
- **Config B — hybrid + RRF:** Chroma cosine cộng BM25Plus, gộp một lần bằng RRF (`k=60`), `top_k=5`.

Hai cấu hình dùng cùng 17 câu hỏi và cùng bộ tạo câu trả lời trích nguyên văn. File [metrics.json](metrics.json) lưu kết quả từng câu. Chạy lại bằng `python -m group_project.evaluation.evaluate` từ thư mục repo.

## Overall scores

Các số dưới đây là **proxy offline**, không phải kết quả RAGAS hoặc đánh giá của con người:

- Faithfulness: 1 nếu câu trích (chuẩn hóa khoảng trắng) thực sự nằm trong chunk được dẫn ID, ngược lại 0.
- Answer relevance: tỷ lệ từ khóa của đáp án chuẩn xuất hiện trong câu trả lời.
- Context recall: tỷ lệ từ khóa của context chuẩn xuất hiện trong các chunk truy xuất.
- Context precision: tỷ lệ chunk thuộc đúng file nguồn trong top 5.

Phép đo từ khóa quy đổi `24TC` thành `24 tín chỉ` trước khi so khớp. Chế độ demo offline chỉ dò thêm trong các file đã xuất hiện ở kết quả truy xuất ban đầu; chunk dẫn nguồn được đưa vào danh sách nguồn trả về.

| Metric | Config A | Config B | Delta B−A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0,9412 | 1,0000 | +0,0588 |
| Answer relevance | 0,7274 | 0,9012 | +0,1738 |
| Context recall | 0,8742 | 1,0000 | +0,1258 |
| Context precision | 0,4824 | 0,5882 | +0,1058 |
| **Average** | **0,7563** | **0,8724** | **+0,1161** |

## A/B comparison

Hybrid + RRF có trung bình proxy cao hơn 0,1161. Latency trung bình sau khi đã nạp model là 0,118 giây/câu cho dense-only và 0,063 giây/câu cho hybrid trong lần chạy này; chênh lệch nhỏ và không nên coi là kết luận về tốc độ. Cả hai cấu hình đều dùng embedding cục bộ và không gọi API trả phí.

## Worst performers

| # | Câu hỏi | Cấu hình | Faithfulness | Relevance | Recall | Precision | Nguyên nhân |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Kỳ 2025.2 đăng ký tối đa bao nhiêu tín chỉ? | B | 1,0000 | 0,6667 | 1,0000 | 0,2000 | Trích đúng dòng 24TC/28TC nhưng bốn chunk khác trong top 5 thuộc nguồn khác. |
| 2 | Bao nhiêu sinh viên được học bổng kỳ I 2025-2026? | B | 1,0000 | 1,0000 | 1,0000 | 0,2000 | Trích đúng con số 1.309 nhưng chỉ một chunk trong top 5 thuộc bài thông báo. |
| 3 | K70 có cần đăng ký học phần kỳ 2025.2? | B | 1,0000 | 0,6923 | 1,0000 | 0,6000 | Câu trích dùng viết tắt CTĐT nên proxy từ khóa thấp hơn dù nội dung chính có mặt. |

## Recommendations

1. Giảm nhiễu từ các chunk nguồn khác cho câu hỏi có số liệu; đo lại context precision trên cùng 17 câu.
2. Loại phần menu, liên kết và nội dung phụ từ bài web trước khi chunk/index lại; kiểm tra các câu hỏi về thư viện.
3. Bổ sung câu hỏi ngoài miền để hiệu chỉnh ngưỡng fallback 0,3; kiểm tra câu từ chối và nguồn trước buổi demo.
4. Nếu có API key, chạy thêm RAGAS hoặc đánh giá con người và ghi riêng kết quả; proxy hiện tại chỉ đo khớp từ và file nguồn.

## Bonus experiments

Chưa chạy reranker ngoài RRF. PageIndex và LLM bên ngoài chưa được đo vì môi trường hiện tại chưa cấu hình API key; demo offline vẫn chạy bằng truy xuất hybrid và trích dẫn nguyên văn.
