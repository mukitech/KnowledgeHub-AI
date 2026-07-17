from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "KnowledgeHub AI Backend Running"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
