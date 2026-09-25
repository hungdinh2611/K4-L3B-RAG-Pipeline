"""Offline, reproducible A/B retrieval evaluation for the lab corpus.

The four numbers are transparent lexical/source proxies, not RAGAS or human
judgments. No provider key or network connection is required.
"""

import json
import re
import time
from pathlib import Path

from src.task10_generation import SAFE_REFUSAL, _local_evidence, _terms
from src.task9_retrieval_pipeline import retrieve


HERE = Path(__file__).parent
DATASET_PATH = HERE / "golden_dataset.json"
OUTPUT_PATH = HERE / "metrics.json"
TOP_K = 5


def _fraction(found: set[str], expected: set[str]) -> float:
    return len(found & expected) / len(expected) if expected else 0.0


def _faithful(answer: str, chunks: list[dict]) -> float:
    match = re.search(r"“(.*?)” \[(.*?)\]$", answer, flags=re.DOTALL)
    if not match:
        return 0.0
    excerpt, cited_id = match.groups()
    normalized_excerpt = re.sub(r"\s+", " ", excerpt).strip()
    return float(any(
        item["id"] == cited_id
        and normalized_excerpt in re.sub(r"\s+", " ", item["content"])
        for item in chunks
    ))


def evaluate_case(case: dict, use_reranking: bool) -> dict:
    started = time.perf_counter()
    retrieved = retrieve(
        case["question"], top_k=TOP_K, score_threshold=-1.0,
        use_reranking=use_reranking,
    )
    answer, chunks = _local_evidence(case["question"], retrieved, TOP_K) if retrieved else (SAFE_REFUSAL, [])
    elapsed = time.perf_counter() - started
    context_terms = _terms(" ".join(item["content"] for item in chunks))
    answer_terms = _terms(answer) if answer != SAFE_REFUSAL else set()
    scores = {
        "faithfulness": _faithful(answer, chunks),
        "answer_relevance": _fraction(answer_terms, _terms(case["expected_answer"])),
        "context_recall": _fraction(context_terms, _terms(case["expected_context"])),
        "context_precision": (
            sum(item["metadata"]["source"] == case["source"] for item in chunks) / len(chunks)
            if chunks else 0.0
        ),
    }
    return {
        "question": case["question"],
        "expected_source": case["source"],
        "answer": answer,
        "source_ids": [item["id"] for item in chunks],
        "latency_seconds": round(elapsed, 3),
        "scores": {name: round(value, 4) for name, value in scores.items()},
    }


def main() -> None:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    from src.task4_chunking_indexing import embed_texts

    embed_texts(["warmup"])
    configs = {
        "dense_only": [evaluate_case(case, False) for case in cases],
        "hybrid_rrf": [evaluate_case(case, True) for case in cases],
    }
    summary = {}
    for name, rows in configs.items():
        summary[name] = {
            metric: round(sum(row["scores"][metric] for row in rows) / len(rows), 4)
            for metric in ("faithfulness", "answer_relevance", "context_recall", "context_precision")
        }
        summary[name]["mean_latency_seconds"] = round(
            sum(row["latency_seconds"] for row in rows) / len(rows), 3
        )
    result = {"dataset_size": len(cases), "top_k": TOP_K, "summary": summary, "cases": configs}
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
