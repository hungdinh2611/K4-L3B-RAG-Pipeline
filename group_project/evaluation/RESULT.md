# Kết quả đánh giá RAG

## Run information

| Trường | Giá trị |
| --- | --- |
| Ngày chạy | 2026-09-25 |
| Framework | `group_project/evaluation/evaluate.py` (đánh giá offline) |
| Evaluator | Quy tắc đối chiếu nguồn và từ khóa; không sử dụng LLM judge |
| Generator | Trích nguyên văn từ chunk có citation khi chưa có API key |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Corpus | 8 tài liệu, 450 chunk; commit nền `f9a5c2e` cùng dữ liệu làm việc hiện tại |
| Golden dataset | 17 câu hỏi có đáp án, context và tên nguồn |
| `top_k` | 5 |
| Fallback threshold | Không áp dụng cho so sánh A/B (`score_threshold=-1`); mặc định demo 0,3, chưa hiệu chỉnh trên tập ngoài miền đủ lớn |

## Configurations

- **Config A — dense-only:** Chroma cosine, cùng embedding và `top_k=5`.
- **Config B — hybrid + RRF:** Chroma cosine cộng BM25Plus, gộp một lần bằng RRF (`k=60`), `top_k=5`.

Hai cấu hình dùng cùng 17 câu hỏi và cùng bộ tạo câu trả lời trích nguyên văn. File [metrics.json](metrics.json) lưu kết quả từng câu. Chạy lại bằng `python -m group_project.evaluation.evaluate` từ thư mục repo.

## Overall scores

Các số dưới đây là **proxy offline**, không phải kết quả RAGAS hoặc đánh giá của con người:

- Faithfulness: 1 nếu câu trích nguyên văn thực sự nằm trong chunk được dẫn ID, ngược lại 0.
- Answer relevance: tỷ lệ từ khóa của đáp án chuẩn xuất hiện trong câu trả lời.
- Context recall: tỷ lệ từ khóa của context chuẩn xuất hiện trong các chunk truy xuất.
- Context precision: tỷ lệ chunk thuộc đúng file nguồn trong top 5.

| Metric | Config A | Config B | Delta B−A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0,9412 | 0,9412 | 0,0000 |
| Answer relevance | 0,5944 | 0,6154 | +0,0210 |
| Context recall | 0,8566 | 0,9275 | +0,0709 |
| Context precision | 0,4471 | 0,5294 | +0,0823 |
| **Average** | **0,7098** | **0,7534** | **+0,0436** |

## A/B comparison

Hybrid + RRF có trung bình proxy cao hơn 0,0436, chủ yếu do context recall và context precision. Latency trung bình sau khi đã nạp model là 0,073 giây/câu cho dense-only và 0,071 giây/câu cho hybrid trong lần chạy này; chênh lệch nhỏ và không nên coi là kết luận về tốc độ. Cả hai cấu hình đều dùng embedding cục bộ và không gọi API trả phí.

## Worst performers

| # | Câu hỏi | Cấu hình | Faithfulness | Relevance | Recall | Precision | Nguyên nhân |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Học bổng loại xuất sắc bằng bao nhiêu phần trăm học phí? | B | 0,0000 | 0,0000 | 0,6667 | 0,4000 | Bộ trích dẫn không chọn được dòng chứa tỷ lệ dù nguồn đã được truy xuất. |
| 2 | Học phí năm học 2025-2026 được tính theo gì? | B | 1,0000 | 0,2222 | 0,5000 | 0,4000 | Dòng được trích liên quan năm học nhưng chưa chứa quy tắc tính theo tín chỉ. |
| 3 | Thời gian đăng ký học phần kỳ 2025.2 là khi nào? | B | 1,0000 | 0,2000 | 0,6000 | 0,4000 | Bộ trích dẫn chọn dòng tiêu đề thay vì dòng có ngày giờ. |

## Recommendations

1. Cải thiện bộ chọn đoạn trích bằng cách ưu tiên số liệu và ngày giờ khi câu hỏi hỏi “bao nhiêu” hoặc “khi nào”; kiểm tra lại ba câu tệ nhất.
2. Loại phần menu, liên kết và nội dung phụ từ bài web trước khi chunk/index lại; đo context precision theo cùng tập 17 câu.
3. Bổ sung câu hỏi ngoài miền để hiệu chỉnh ngưỡng fallback 0,3; kiểm tra câu từ chối và nguồn trước buổi demo.
4. Nếu có API key, chạy thêm RAGAS hoặc đánh giá con người và ghi riêng kết quả; proxy hiện tại chỉ đo khớp từ và file nguồn.

## Bonus experiments

Chưa chạy reranker ngoài RRF. PageIndex và LLM bên ngoài chưa được đo vì môi trường hiện tại chưa cấu hình API key; demo offline vẫn chạy bằng truy xuất hybrid và trích dẫn nguyên văn.
