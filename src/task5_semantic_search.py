"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    collection = get_collection()
    try:
        collection_size = int(collection.count())
    except (AttributeError, TypeError, ValueError):
        collection_size = top_k
    if collection_size <= 0:
        return []

    query_vector = embed_texts([query])[0]
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection_size),
        include=["documents", "metadatas", "distances"],
    )
    results = []
    for item_id, content, metadata, distance in zip(
        response.get("ids", [[]])[0],
        response.get("documents", [[]])[0],
        response.get("metadatas", [[]])[0],
        response.get("distances", [[]])[0],
    ):
        item_metadata = dict(metadata)
        if item_metadata.get("url") == "":
            item_metadata["url"] = None
        results.append({
            "id": item_id,
            "content": content,
            "score": max(0.0, float(1.0 - distance)),
            "metadata": item_metadata,
            "retrieval_method": "dense",
        })
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
