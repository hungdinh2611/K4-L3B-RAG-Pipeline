"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 4/5 (load lại từ data/standardized/ qua
load_documents() + chunk_documents(), không kèm embedding). BM25 phù hợp với
từ khóa chính xác, mã tài liệu và tên riêng. Output phải theo SearchResult và
sort score giảm dần.
"""

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []

# Cache theo id(CORPUS): tự rebuild khi CORPUS bị gán lại (kể cả qua
# monkeypatch trong test), nhưng không rebuild lại mỗi lần gọi lexical_search
# trong cùng một phiên chạy thật.
_bm25_cache: tuple[int, object] | None = None


def load_corpus() -> list[dict]:
    """Nạp lại đúng tập chunk mà Task 4 đã index (không cần embedding)."""
    global CORPUS
    CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


def _get_bm25_index():
    global _bm25_cache
    if _bm25_cache is None or _bm25_cache[0] != id(CORPUS):
        _bm25_cache = (id(CORPUS), build_bm25_index(CORPUS))
    return _bm25_cache[1]


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not CORPUS:
        return []

    bm25 = _get_bm25_index()
    scores = bm25.get_scores(query.lower().split())

    # Sort tường minh: score giảm dần, tie-break theo index gốc tăng dần.
    # np.argsort(...)[::-1] KHÔNG đảm bảo stable khi có score bằng nhau (vd.
    # BM25 idf = 0 khi 1 từ khóa xuất hiện đúng nửa số document) — dùng cách
    # này để thứ tự luôn xác định (deterministic), không phụ thuộc thuật toán
    # sort nội bộ của numpy.
    order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))[:top_k]

    # Lưu ý: không lọc theo "score <= 0". Với corpus nhỏ, BM25 idf có thể = 0
    # khi 1 từ khóa xuất hiện ở đúng một nửa số document (log((N-n+0.5)/(n+0.5))
    # = 0 khi n = N/2) — đây KHÔNG có nghĩa là chunk không liên quan, và lọc bỏ
    # sẽ làm sai thứ hạng/số lượng kết quả trả về so với top_k yêu cầu.
    results = []
    for index in order:
        score = float(scores[index])
        item = CORPUS[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": score,
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )

    return results


if __name__ == "__main__":
    load_corpus()
    print(f"Loaded {len(CORPUS)} chunks for BM25")
    for result in lexical_search("học phí tín chỉ", top_k=3):
        print(result["score"], "-", result["metadata"].get("title"), "-", result["id"])