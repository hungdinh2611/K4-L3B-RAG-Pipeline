"""Optional PageIndex fallback for the original legal PDF documents."""

import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

ROOT = Path(__file__).parent.parent
LEGAL_DIR = ROOT / "data" / "landing" / "legal"
CACHE_PATH = ROOT / "data" / "pageindex_document_ids.json"
BASE_URL = "https://api.pageindex.ai"
REQUEST_TIMEOUT = 15
POLL_SECONDS = 1
MAX_POLLS = 15


def _key() -> str:
    return os.getenv("PAGEINDEX_API_KEY", "").strip()


def _request(method: str, path: str, **kwargs) -> dict:
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers={"api_key": _key()},
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def _cached_documents() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        value = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def upload_documents() -> None:
    """Upload changed legal PDFs once, caching their PageIndex document IDs."""
    if not _key():
        return

    cached = _cached_documents()
    for path in sorted(LEGAL_DIR.glob("*.pdf")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if cached.get(path.name, {}).get("sha256") == digest:
            continue
        with path.open("rb") as document:
            payload = _request(
                "POST", "/doc/", files={"file": (path.name, document)},
                data={"if_retrieval": "true"},
            )
        doc_id = payload.get("doc_id")
        if not doc_id:
            raise ValueError(f"PageIndex did not return doc_id for {path.name}")
        cached[path.name] = {"doc_id": str(doc_id), "sha256": digest}
        CACHE_PATH.write_text(
            json.dumps(cached, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Query cached PageIndex PDFs and return ranked SearchResult items."""
    if not _key() or top_k <= 0 or not query.strip():
        return []

    cached = _cached_documents()
    if not cached:
        return []

    results: list[dict] = []
    for filename, document in cached.items():
        doc_id = document.get("doc_id")
        if not doc_id:
            continue
        try:
            submitted = _request(
                "POST", "/retrieval/",
                json={"doc_id": doc_id, "query": query, "thinking": False},
            )
            retrieval_id = submitted.get("retrieval_id")
            if not retrieval_id:
                continue
            response = {}
            for _ in range(MAX_POLLS):
                response = _request("GET", f"/retrieval/{retrieval_id}/")
                if response.get("status") in {"completed", "failed", "error"}:
                    break
                time.sleep(POLL_SECONDS)
            if response.get("status") != "completed":
                continue
        except (requests.RequestException, ValueError):
            continue

        for node_index, node in enumerate(response.get("retrieved_nodes") or []):
            contents = node.get("relevant_contents") or []
            for content_index, passage in enumerate(contents):
                if isinstance(passage, str):
                    text = passage.strip()
                    page_index = 0
                else:
                    text = str(passage.get("relevant_content") or "").strip()
                    page_index = passage.get("page_index", 0)
                if not text:
                    continue
                page_index = page_index if isinstance(page_index, int) and page_index >= 0 else 0
                results.append({
                    "id": f"pageindex/{doc_id}/{node.get('node_id', node_index)}/{content_index}",
                    "content": text,
                    "score": 1.0 / (len(results) + 1),
                    "metadata": {
                        "source": filename,
                        "title": str(node.get("title") or Path(filename).stem),
                        "doc_type": "legal",
                        "url": None,
                        "chunk_index": page_index,
                    },
                    "retrieval_method": "pageindex",
                })
    return results[:top_k]


if __name__ == "__main__":
    upload_documents()
