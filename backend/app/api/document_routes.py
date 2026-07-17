from fastapi import APIRouter, File, UploadFile

from app.services.document_service import save_upload_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    return await save_upload_document(file)
