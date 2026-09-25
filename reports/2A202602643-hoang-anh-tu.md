# Báo cáo đóng góp cá nhân — Hoàng Anh Tú

## Thông tin

- Họ và tên: Hoàng Anh Tú
- Mã học viên: 2A202602643
- Nhóm: K4-L3B
- Repository/branch: `K4-L3B-RAG-Pipeline` / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Báo cáo evaluation | Biên soạn và phân tích kết quả A/B dense-only với hybrid + RRF; tổng hợp metric, worst performers, nguyên nhân và khuyến nghị từ kết quả của nhóm | `group_project/evaluation/RESULT.md`, `reports/RESULT.md` | Done |

Phần chạy evaluation và tạo dữ liệu/metrics được ghi riêng cho thành viên phụ trách evaluation. Phần việc của tôi là trình bày, diễn giải kết quả và nêu giới hạn của phép đo trong báo cáo.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Ghi rõ bốn metric trong báo cáo là proxy offline, không phải kết quả RAGAS hay human evaluation.  
   **Lý do/evidence:** `RESULT.md` mô tả các phép đo dựa trên trích dẫn, từ khóa và file nguồn; cách này giúp người đọc hiểu đúng phạm vi của điểm số.  
   **Trade-off:** Báo cáo có thể so sánh hai cấu hình trên cùng tập câu hỏi, nhưng proxy không đánh giá đầy đủ chất lượng ngữ nghĩa.

2. **Quyết định:** Phân tích riêng các worst performers và gắn nguyên nhân với nhiễu context, thay vì kết luận chỉ từ điểm trung bình.  
   **Lý do/evidence:** Một số câu có context recall cao nhưng context precision thấp do top 5 chứa chunk từ nguồn khác.  
   **Trade-off:** Phân tích thủ công tốn thời gian và phụ thuộc vào cách chọn các case đại diện.

## Kiểm thử và kết quả

- Đối chiếu phần tổng hợp trong `RESULT.md` với 17 case trong `golden_dataset.json` và kết quả từng case trong `metrics.json`.
- Báo cáo ghi nhận average proxy của hybrid + RRF là `0,8724`, cao hơn dense-only `0,7563` (`+0,1161`); latency trong lần chạy này lần lượt là `0,063` và `0,118` giây/câu.
- Nêu các giới hạn còn lại: proxy offline, cần thêm câu hỏi ngoài miền để hiệu chỉnh threshold, và cần human evaluation hoặc RAGAS nếu có điều kiện.

## Điều còn hạn chế

- Báo cáo dựa trên một bộ 17 câu hỏi; kết luận chưa đại diện cho mọi câu hỏi hoặc corpus.
- Nếu có thêm thời gian, mở rộng tập ngoài miền và tổ chức human evaluation, sau đó cập nhật phân tích worst performers và khuyến nghị.

## Xác nhận đóng góp

Tôi xác nhận phần mô tả trên phản ánh phần việc báo cáo mà tôi phụ trách.

- Ngày: 2026-09-25
- Tên thành viên: Hoàng Anh Tú
