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

import re
from pathlib import Path


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Recursive character splitting: ưu tiên cắt theo đoạn -> dòng -> câu -> khoảng
# trắng, chỉ rơi xuống mức nhỏ hơn khi đoạn vẫn vượt CHUNK_SIZE. Phù hợp với
# corpus lệch loại (văn bản pháp lý nhiều Điều/Khoản dài + bài viết web ngắn)
# vì không cắt cứng theo số ký tự, giữ nguyên câu/đoạn khi có thể.
# 500 ký tự đủ nhỏ để định vị đúng 1 ý (vd. 1 mức học phí cụ thể) mà không kéo
# theo cả văn bản; overlap 50 (10%) giữ ngữ cảnh nối câu giữa 2 chunk liền kề
# mà không đội chi phí embedding đáng kể. Giải thích chi tiết xem báo cáo.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

# Header do Task 3 ghi vào đầu mỗi file Markdown chuẩn hóa, ngăn cách với
# nội dung thật bằng "---". Parse lại header để lấy title/url gốc, giữ khả
# năng truy ngược từ chunk -> document -> nguồn công khai.
_HEADER_SEPARATOR = "\n---\n\n"
_TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_URL_PATTERN = re.compile(r"\*\*Source:\*\*\s*(\S+)")

_embedding_model = None


def _split_header(raw_text: str) -> tuple[str | None, str | None, str]:
    """Tách header (title/url) khỏi nội dung chính của file Markdown."""
    if _HEADER_SEPARATOR not in raw_text:
        return None, None, raw_text.strip()

    header, body = raw_text.split(_HEADER_SEPARATOR, 1)
    title_match = _TITLE_PATTERN.search(header)
    url_match = _URL_PATTERN.search(header)
    title = title_match.group(1).strip() if title_match else None
    url = url_match.group(1).strip() if url_match else None
    return title, url, body.strip()


def load_documents() -> list[dict]:
    """Đọc Markdown trong data/standardized/ và trả về danh sách Document."""
    documents = []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        title, url, content = _split_header(raw_text)

        if not content:
            continue

        doc_type = "legal" if "legal" in path.parts else "news"

        documents.append(
            {
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": content,
                "metadata": {
                    "source": path.name,
                    "title": title or path.stem,
                    "doc_type": doc_type,
                    "url": url,
                },
            }
        )

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id ổn định và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for document in documents:
        pieces = [piece.strip() for piece in splitter.split_text(document["content"])]
        for index, text in enumerate(piece for piece in pieces if piece):
            chunks.append(
                {
                    # ID ổn định qua các lần chạy lại: <đường dẫn document>::chunk-<index>.
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )

    return chunks


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách text bằng một provider duy nhất (dùng chung Task 4 & 5)."""
    if not texts:
        return []

    model = _get_embedding_model()
    # normalize_embeddings=True vì collection dùng cosine distance: vector đã
    # chuẩn hóa giúp dense score = 1 - distance tương ứng đúng cosine similarity.
    vectors = model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
    return [vector.tolist() for vector in vectors]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk, giữ nguyên các field khác."""
    if not chunks:
        return []

    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def get_collection():
    """Mở (hoặc tạo) Chroma persistent collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _sanitize_metadata(metadata: dict) -> dict:
    """ChromaDB không chấp nhận giá trị None trong metadata -> đổi thành ''."""
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB theo id ổn định (chạy lại không nhân bản)."""
    if not chunks:
        return

    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[_sanitize_metadata(chunk["metadata"]) for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")

    chunks = chunk_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks into '{COLLECTION_NAME}'")


if __name__ == "__main__":
    run_pipeline()