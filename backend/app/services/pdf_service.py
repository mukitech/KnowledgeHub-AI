from pathlib import Path
from typing import Any, Dict, List

import fitz
from fastapi import HTTPException, status


def extract_pages(file_path: str) -> List[Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found",
        )

    try:
        document = fitz.open(path)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted PDF",
        ) from exc

    if document.is_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password-protected PDF",
        )

    pages = []
    for index, page in enumerate(document, start=1):
        text = page.get_text().strip()
        if text:
            pages.append({"page_number": index, "text": text})

    document.close()

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty PDF",
        )

    return pages


def extract_text(file_path: str) -> str:
    pages = extract_pages(file_path)
    return "\n\n".join(page["text"] for page in pages)

