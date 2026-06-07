import math
import os
import time
import uuid

import httpx
from fastapi import HTTPException

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
SEARCH_RADIUS_M = 25000.0  # ~15 miles
PLACES_TIMEOUT = httpx.Timeout(connect=2.0, read=6.0, write=2.0, pool=2.0)


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _top_shops(shops: list[dict], n: int = 5) -> list[dict]:
    """Return the top-n shops ranked by a combined rating + proximity score.

    Rating is adjusted via a Bayesian average before normalization, so shops
    with very few reviews are pulled toward the global prior (3.5 stars) and
    can't inflate their score with a handful of outlier reviews.

    Score = 0.5 * norm_bayesian_rating + 0.5 * norm_proximity  (both in [0, 1])
    Shops with no rating fall back to the prior rating.
    """
    if not shops:
        return shops

    PRIOR_RATING = 3.5   # assumed global average for ski/board shops
    PRIOR_COUNT = 25     # weight of the prior in review-count units

    max_dist = max(s["distance_miles"] for s in shops) or 1.0

    def score(shop: dict) -> float:
        rating = shop["rating"] if shop["rating"] is not None else PRIOR_RATING
        count = shop["user_rating_count"] or 0
        bayesian_rating = (rating * count + PRIOR_RATING * PRIOR_COUNT) / (count + PRIOR_COUNT)
        norm_rating = (bayesian_rating - 1.0) / 4.0                    # 1–5 → 0–1
        norm_proximity = 1.0 - (shop["distance_miles"] / max_dist)     # closer → higher
        return 0.5 * norm_rating + 0.5 * norm_proximity

    return sorted(shops, key=score, reverse=True)[:n]


async def find_nearest_shops(lat: float, lon: float, ranked: bool = False) -> list[dict]:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("[shops] ERROR: GOOGLE_PLACES_API_KEY environment variable not set")
        raise HTTPException(status_code=503, detail="GOOGLE_PLACES_API_KEY is not configured on the server.")

    request_id = uuid.uuid4().hex[:8]
    request_started_at = time.perf_counter()
    print(f"[shops:{request_id}] Request received: lat={lat}, lon={lon}")

    payload = {
        "textQuery": "ski snowboard shop rental repair",
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": SEARCH_RADIUS_M,
            }
        },
        "maxResultCount": 20,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.location,"
            "places.rating,"
            "places.userRatingCount"
        ),
    }

    print(f"[shops:{request_id}] Sending Places API request: {payload}")

    try:
        places_started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=PLACES_TIMEOUT) as client:
            resp = await client.post(PLACES_URL, json=payload, headers=headers)
            print(
                f"[shops:{request_id}] Places API response status: {resp.status_code} "
                f"after {round((time.perf_counter() - places_started_at) * 1000)} ms"
            )
            if not resp.is_success:
                print(f"[shops:{request_id}] Places API error body: {resp.text}")
            resp.raise_for_status()
    except httpx.TimeoutException as exc:
        elapsed_ms = round((time.perf_counter() - request_started_at) * 1000)
        print(f"[shops:{request_id}] Places API timeout after {elapsed_ms} ms: {exc}")
        raise HTTPException(status_code=504, detail="Places API timed out. Please try again.")
    except httpx.HTTPError as exc:
        elapsed_ms = round((time.perf_counter() - request_started_at) * 1000)
        print(f"[shops:{request_id}] Places API HTTP error after {elapsed_ms} ms: {exc}")
        raise HTTPException(status_code=502, detail=f"Places API error: {exc}")

    places = resp.json().get("places", [])
    print(f"[shops:{request_id}] Places API returned {len(places)} results")

    shops = []
    for place in places:
        name = place.get("displayName", {}).get("text")
        location = place.get("location", {})
        plat = location.get("latitude")
        plon = location.get("longitude")

        if not name or plat is None:
            print(f"[shops:{request_id}] Skipping (missing name or location): {place}")
            continue

        dist = round(_haversine_miles(lat, lon, plat, plon), 1)
        print(f"[shops:{request_id}] Adding: {name!r} at {dist} mi")
        shops.append({
            "name": name,
            "distance_miles": dist,
            "lat": plat,
            "lon": plon,
            "address": place.get("formattedAddress"),
            "phone": place.get("nationalPhoneNumber"),
            "website": place.get("websiteUri"),
            "rating": place.get("rating"),
            "user_rating_count": place.get("userRatingCount"),
        })

    shops = _top_shops(shops) if ranked else sorted(shops, key=lambda s: s["distance_miles"])
    print(
        f"[shops:{request_id}] Returning {len(shops)} shops "
        f"after {round((time.perf_counter() - request_started_at) * 1000)} ms"
    )
    return shops
