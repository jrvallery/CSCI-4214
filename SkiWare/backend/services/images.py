import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"


async def save_image(file: UploadFile) -> str:
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP, and GIF images are supported.",
        )
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be under 10 MB.",
        )
    ext = Path(file.filename or "image").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    UPLOADS_DIR.mkdir(exist_ok=True)
    (UPLOADS_DIR / filename).write_bytes(content)
    return f"/uploads/{filename}"
