"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề: Dịch vụ đại học (Đại học Bách Khoa Hà Nội - HUST)
Nguồn: cổng thông tin đào tạo công khai của HUST (ctt.hust.edu.vn, hust.edu.vn).
"""

from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Tên file (không dấu) -> URL nguồn công khai.
SOURCES = {
    "hust-quyet-dinh-hoc-phi-2025-2026.pdf": (
        "https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20"
        "%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hocphi/2025-2026/"
        "QD%20HOC%20PHI%20-%202025-2026-final.pdf"
    ),
    "hust-quy-che-dao-tao-2025.pdf": (
        "https://ctt.hust.edu.vn/Upload/Nguy%E1%BB%85n%20Qu%E1%BB%91c%20"
        "%C4%90%E1%BA%A1t/files/DTDH_QDQC/Hoctap/"
        "QCDT_2025_5445_QD-DHBK.pdf"
    ),
    # Quy định về học bổng khuyến khích học tập cho sinh viên (văn bản chung,
    # domain khác hoàn toàn với hust.edu.vn để tránh phụ thuộc DNS của 1 domain).
    "quy-dinh-hoc-bong-khuyen-khich-hoc-tap.pdf": (
        "https://pctsv.hcmulaw.edu.vn/Resources/Docs/SubDomain/pctsv/"
        "uoloadNewFolder/B%E1%BB%98%20C%C3%94NG%20C%E1%BB%A4%20C%E1%BB%90"
        "%20V%E1%BA%A4N%20H%E1%BB%8CC%20T%E1%BA%ACP/Quy%20%C4%91%E1%BB%8Bnh"
        "%20V%E1%BB%81%20h%E1%BB%8Dc%20b%E1%BB%95ng%20khuy%E1%BA%BFn"
        "%20kh%C3%ADch%20h%E1%BB%8Dc%20t%E1%BA%ADp%20cho%20sinh%20vi%C3%AAn.pdf"
    ),
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải tối thiểu 3 PDF/DOCX từ nguồn công khai vào DATA_DIR."""
    headers = {
        # Một số WAF chặn request không có User-Agent trình duyệt.
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    for filename, url in SOURCES.items():
        destination = DATA_DIR / filename
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            destination.write_bytes(response.content)
            size_kb = destination.stat().st_size / 1024
            print(f"Saved: {destination} ({size_kb:.1f} KB)")
        except requests.RequestException as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    setup_directory()
    download_documents()