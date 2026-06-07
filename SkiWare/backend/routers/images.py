from fastapi import APIRouter, File, UploadFile

from backend.services.images import save_image

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> dict:
    url = await save_image(file)
    return {"url": url}
