from fastapi import APIRouter, Query

from backend.services.shops import find_nearest_shops

router = APIRouter(prefix="/api", tags=["shops"])


@router.get("/shops/nearest")
async def nearest_shops(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    ranked: bool = Query(False),
):
    return await find_nearest_shops(lat, lon, ranked=ranked)
