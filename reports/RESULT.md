# Kết quả đánh giá

Báo cáo chính thức nằm tại [`group_project/evaluation/RESULT.md`](../group_project/evaluation/RESULT.md).

Kết quả mới nhất dùng 17 câu hỏi golden, so sánh dense-only với hybrid + RRF trên cùng `top_k=5`. Chi tiết từng câu và latency được lưu tại [`group_project/evaluation/metrics.json`](../group_project/evaluation/metrics.json).

Chạy lại từ thư mục gốc:

```bash
python -m group_project.evaluation.evaluate
```
