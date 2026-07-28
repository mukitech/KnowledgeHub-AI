from typing import Any, Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(
    pages: List[Dict[str, Any]], chunk_size: int = 500, chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """Split page-indexed text blocks while preserving page numbers and character offsets."""
    if not pages:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    result: List[Dict[str, Any]] = []
    global_chunk_index = 0

    for page in pages:
        page_number = page.get("page_number", 1)
        page_text = page.get("text", "")
        if not page_text or not page_text.strip():
            continue

        chunks = splitter.split_text(page_text)
        cursor = 0
        for chunk in chunks:
            start = page_text.find(chunk, cursor)
            if start == -1:
                start = cursor

            end = start + len(chunk)
            result.append(
                {
                    "chunk_index": global_chunk_index,
                    "chunk_text": chunk,
                    "page_number": page_number,
                    "character_start": start,
                    "character_end": end,
                }
            )
            global_chunk_index += 1
            cursor = end

    return result


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
    """Fallback chunking for raw text without explicit page boundaries."""
    return chunk_pages([{"page_number": 1, "text": text}], chunk_size=chunk_size, chunk_overlap=chunk_overlap)

