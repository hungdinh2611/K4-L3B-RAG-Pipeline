"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []
_bm25_cache: tuple[int, object] | None = None


def load_corpus() -> list[dict]:
    """Load the same chunks used for vector indexing, without embeddings."""
    global CORPUS, _bm25_cache
    CORPUS = chunk_documents(load_documents())
    _bm25_cache = None
    return CORPUS


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Plus

    return BM25Plus([_tokens(item["content"]) for item in corpus])


def _get_bm25_index(corpus: list[dict]):
    global _bm25_cache
    if _bm25_cache is None or _bm25_cache[0] != id(corpus):
        _bm25_cache = (id(corpus), build_bm25_index(corpus))
    return _bm25_cache[1]


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    corpus = CORPUS if CORPUS else load_corpus()
    if not corpus:
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    bm25 = _get_bm25_index(corpus)
    scores = bm25.get_scores(query_tokens)
    indices = sorted(range(len(corpus)), key=lambda index: (-scores[index], index))
    results = []
    seen_ids: set[str] = set()
    query_token_set = set(query_tokens)
    for index in indices:
        if len(results) >= top_k:
            break
        if scores[index] <= 0:
            break
        item = corpus[index]
        if not query_token_set.intersection(_tokens(item["content"])):
            continue
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
    return results


if __name__ == "__main__":
    load_corpus()
    print(f"Loaded {len(CORPUS)} chunks for BM25")
    for result in lexical_search("học phí tín chỉ", top_k=3):
        print(result["score"], "-", result["metadata"].get("title"), "-", result["id"])
