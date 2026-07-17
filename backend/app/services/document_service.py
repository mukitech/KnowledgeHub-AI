from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_document(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected",
        )

    filename = file.filename.lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    extension = Path(file.filename).suffix.lower()
    saved_filename = f"{uuid4().hex}{extension}"
    save_path = UPLOAD_DIR / saved_filename

    with save_path.open("wb") as destination:
        destination.write(content)

    return {
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "file_size": len(content),
    }
