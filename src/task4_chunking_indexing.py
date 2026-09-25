"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .contracts import validate_document

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Cấu hình chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# Cấu hình embedding model
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDING_DIM = 384

COLLECTION_NAME = "rag_documents"
_HEADER_SEPARATOR = "\n---\n"
_TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_URL_PATTERN = re.compile(r"\*\*Source:\*\*\s*(\S+)")

_EMBEDDING_MODEL_INSTANCE: Any = None


def _get_embedding_model():
    """Khởi tạo embedding model một lần và tái sử dụng."""
    global _EMBEDDING_MODEL_INSTANCE
    if _EMBEDDING_MODEL_INSTANCE is None:
        if EMBEDDING_PROVIDER == "sentence_transformers":
            from sentence_transformers import SentenceTransformer

            model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
            try:
                # Prefer the local Hugging Face cache so an offline demo does
                # not stall on metadata checks for an already downloaded model.
                _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(
                    model_name, local_files_only=True
                )
            except Exception as exc:
                if os.getenv("EMBEDDING_OFFLINE", "0") == "1":
                    raise RuntimeError(
                        f"Embedding model {model_name} is not cached locally"
                    ) from exc
                _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(model_name)
        else:
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
    return _EMBEDDING_MODEL_INSTANCE


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Tạo embedding vectors cho danh sách text."""
    if not texts:
        return []
    model = _get_embedding_model()
    embeddings = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embeddings.tolist()


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown trong data/standardized/ và trả về danh sách Document."""
    if not STANDARDIZED_DIR.exists():
        return []

    documents: list[dict] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        # Bỏ qua các file ẩn/gitkeep
        if path.name.startswith("."):
            continue

        raw_text = path.read_text(encoding="utf-8").strip()
        if _HEADER_SEPARATOR in raw_text:
            header, content = raw_text.split(_HEADER_SEPARATOR, 1)
            content = content.strip()
        else:
            header, content = raw_text, raw_text
        if not content:
            continue

        doc_type = "legal" if "legal" in path.parts else "news"
        doc_id = path.relative_to(STANDARDIZED_DIR).as_posix()

        # Trích xuất title từ markdown header # ... nếu có
        title_match = _TITLE_PATTERN.search(header)
        title = title_match.group(1).strip() if title_match else path.stem

        # Trích xuất URL từ **Source:** https://... nếu có
        url: str | None = None
        match = _URL_PATTERN.search(header)
        if match:
            candidate_url = match.group(1).strip()
            if candidate_url.startswith("http://") or candidate_url.startswith(
                "https://"
            ):
                url = candidate_url

        metadata = {
            "source": path.name,
            "title": title or path.stem,
            "doc_type": doc_type,
            "url": url,
        }

        doc = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
        }
        validate_document(doc, require_chunk=False)
        documents.append(doc)

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index theo contract."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".\n", ". ", ";\n", "; ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks: list[dict] = []
    for document in documents:
        splits = splitter.split_text(document["content"])
        chunk_idx = 0
        for text in splits:
            chunk_content = text.strip()
            if not chunk_content:
                continue

            chunk = {
                "id": f"{document['id']}::chunk-{chunk_idx}",
                "content": chunk_content,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": chunk_idx,
                },
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
            chunk_idx += 1

    return chunks


def embed_chunks(chunks: list[dict], batch_size: int = 64) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []

    contents = [chunk["content"] for chunk in chunks]
    all_embeddings: list[list[float]] = []

    for i in range(0, len(contents), batch_size):
        batch = contents[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch))

    embedded_chunks: list[dict] = []
    for chunk, vector in zip(chunks, all_embeddings):
        chunk_copy = dict(chunk)
        chunk_copy["embedding"] = vector
        embedded_chunks.append(chunk_copy)

    return embedded_chunks


def _sanitize_metadata_for_chroma(metadata: dict) -> dict:
    """ChromaDB Rust bindings không nhận None; convert None thành rỗng."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            sanitized[key] = ""
        else:
            sanitized[key] = value
    return sanitized


def index_to_vectorstore(chunks: list[dict], batch_size: int = 200) -> None:
    """Upsert chunks vào ChromaDB với ID ổn định để tránh duplicate."""
    if not chunks:
        return

    collection = get_collection()

    # Đảm bảo các chunk đều có embedding
    if "embedding" not in chunks[0]:
        chunks = embed_chunks(chunks)

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        ids = [chunk["id"] for chunk in batch]
        documents = [chunk["content"] for chunk in batch]
        embeddings = [chunk["embedding"] for chunk in batch]
        metadatas = [_sanitize_metadata_for_chroma(chunk["metadata"]) for chunk in batch]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    print("1. Loading documents from standardized directory...")
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")

    print(f"2. Chunking documents (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("3. Embedding chunks...")
    embedded_chunks = embed_chunks(chunks)

    print("4. Indexing to ChromaDB vector store...")
    index_to_vectorstore(embedded_chunks)

    collection = get_collection()
    count = collection.count()
    print(f"Success! ChromaDB collection '{COLLECTION_NAME}' contains {count} items.")

    # Hiển thị metadata của 2 chunk đầu tiên làm mẫu
    if embedded_chunks:
        print("\nSample chunk 0:")
        sample0 = embedded_chunks[0]
        print(f"  ID: {sample0['id']}")
        print(f"  Metadata: {sample0['metadata']}")
        print(f"  Content preview: {sample0['content'][:120]}...\n")


if __name__ == "__main__":
    run_pipeline()
