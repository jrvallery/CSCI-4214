import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers.assessments import router as assessments_router
from backend.routers.auth import router as auth_router
from backend.routers.images import router as images_router
from backend.routers.shops import router as shops_router
from backend.routers.users import router as users_router


app = FastAPI(title="SkiWare")

app.include_router(assessments_router)
app.include_router(auth_router)
app.include_router(images_router)
app.include_router(shops_router)
app.include_router(users_router)

# Serve uploaded equipment images
_UPLOADS = Path(__file__).parent.parent / "uploads"
_UPLOADS.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOADS), name="uploads")

# Serve compiled React frontend (present in production image, absent in local dev)
_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")


if __name__ == "__main__":
    from uvicorn import run

    port = int(os.environ.get("PORT", 8080))
    run("backend.main:app", host="0.0.0.0", port=port)