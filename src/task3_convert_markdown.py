"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Giữ cấu trúc:
    data/standardized/legal/*.md
    data/standardized/news/*.md

Chạy lại an toàn: ghi đè theo tên file gốc (stem), không tạo bản sao.
"""

import json
from pathlib import Path

from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal sang standardized/legal/*.md."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        result = converter.convert(str(path))
        content = result.text_content.strip()

        if not content:
            print(f"Skip (empty content): {path.name}")
            continue

        header = f"# {path.stem}\n\n**Source file:** {path.name}\n\n---\n\n"
        output_path = output_dir / f"{path.stem}.md"
        output_path.write_text(header + content, encoding="utf-8")
        print(f"Converted: {path.name} -> {output_path.name}")


def convert_news_articles() -> None:
    """Convert JSON trong landing/news sang standardized/news/*.md."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        content = data.get("content_markdown", "").strip()
        if not content:
            print(f"Skip (empty content): {path.name}")
            continue

        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        output_path = output_dir / f"{path.stem}.md"
        output_path.write_text(header + content, encoding="utf-8")
        print(f"Converted: {path.name} -> {output_path.name}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()