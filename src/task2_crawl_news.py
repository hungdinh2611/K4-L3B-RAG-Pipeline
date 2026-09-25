"""
Task 2 — Crawl bài viết/thông báo.

Chủ đề: Dịch vụ đại học (HUST) — học bổng, đăng ký học phần, ký túc xá, thư viện.

Cài browser trước khi chạy:
    python -m playwright install chromium
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from crawl4ai import AsyncWebCrawler


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # Học bổng khuyến khích học tập
    "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=46586",
    # Đăng ký kế hoạch học tập / đăng ký học phần
    "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=45580",
    # Kế hoạch đăng ký lớp học kỳ
    "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=43445",
    # Ký túc xá - những điều tân sinh viên cần biết
    "https://ts.hust.edu.vn/tin-tuc/nhung-dieu-tan-sinh-vien-k66-can-biet",
    # Thư viện - câu hỏi thường gặp
    "https://library.hust.edu.vn/vi/node/50",
]


async def crawl_article(url: str) -> dict:
    """Crawl một URL và trả về dict đúng contract (url/title/date_crawled/content_markdown)."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        if not result.success:
            raise RuntimeError(f"Crawl4AI failed for {url}: {result.error_message}")

        title = (result.metadata or {}).get("title") or "Unknown"
        content_markdown = result.markdown.raw_markdown if hasattr(result.markdown, "raw_markdown") else str(result.markdown)

        return {
            "url": url,
            "title": title.strip(),
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": content_markdown.strip(),
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())