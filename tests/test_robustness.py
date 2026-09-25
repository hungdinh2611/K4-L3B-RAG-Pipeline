import math

import pytest

from src.contracts import validate_generation_result, validate_search_results


def _result(item_id: str = "legal/doc.md::chunk-0") -> dict:
    return {
        "id": item_id,
        "content": "Học phí được tính theo tín chỉ.",
        "score": 0.9,
        "metadata": {
            "source": "doc.md",
            "title": "Quy định học phí",
            "doc_type": "legal",
            "url": None,
            "chunk_index": 0,
        },
        "retrieval_method": "hybrid",
    }


def test_generation_validator_rejects_unknown_citation():
    with pytest.raises(ValueError, match="citation"):
        validate_generation_result(
            {
                "answer": "Học phí theo tín chỉ. [unknown-id]",
                "sources": [_result()],
                "retrieval_source": "hybrid",
            }
        )


def test_search_validator_rejects_non_finite_score():
    item = _result()
    item["score"] = math.nan
    with pytest.raises(ValueError, match="finite"):
        validate_search_results([item])


def test_index_removes_stale_ids_before_upsert(monkeypatch):
    import src.task4_chunking_indexing as indexing

    calls = {"deleted": [], "upserted": []}

    class FakeCollection:
        def get(self, **kwargs):
            assert kwargs == {"include": []}
            return {"ids": ["legal/doc.md::chunk-0", "stale-chunk"]}

        def delete(self, *, ids):
            calls["deleted"].extend(ids)

        def upsert(self, *, ids, documents, embeddings, metadatas):
            calls["upserted"].extend(ids)

    chunk = _result()
    chunk.pop("score")
    chunk.pop("retrieval_method")
    chunk["embedding"] = [0.1, 0.2]
    monkeypatch.setattr(indexing, "get_collection", lambda: FakeCollection())

    indexing.index_to_vectorstore([chunk])

    assert calls == {
        "deleted": ["stale-chunk"],
        "upserted": ["legal/doc.md::chunk-0"],
    }
