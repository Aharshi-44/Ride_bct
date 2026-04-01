import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "rideshare-app"

# In-memory cache for repeated queries (not persisted)
_cache: dict[str, list[dict[str, str]]] = {}
_CACHE_MAX_KEYS = 256


def _user_agent() -> str:
    return getattr(settings, "LOCATIONS_NOMINATIM_USER_AGENT", DEFAULT_USER_AGENT).strip() or DEFAULT_USER_AGENT


def _normalize_query(query: str) -> str:
    return " ".join((query or "").split()).strip()


def get_location_from_nominatim(query: str) -> list[dict[str, str]]:
    """
    Search Nominatim (India). Returns up to 5 items:
    [{"display_name": "...", "lat": "...", "lon": "..."}, ...]
    """
    q = _normalize_query(query)
    if len(q) < 3:
        return []

    cache_key = q.lower()
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params={
                "q": q,
                "format": "json",
                "countrycodes": "in",
                "limit": 5,
            },
            headers={"User-Agent": _user_agent()},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.warning("Nominatim request failed: %s", exc)
        return []

    if not isinstance(data, list) or not data:
        return []

    out: list[dict[str, str]] = []
    for item in data[:5]:
        if not isinstance(item, dict):
            continue
        display_name = item.get("display_name")
        lat = item.get("lat")
        lon = item.get("lon")
        if display_name is None or lat is None or lon is None:
            continue
        out.append(
            {
                "display_name": str(display_name),
                "lat": str(lat),
                "lon": str(lon),
            }
        )

    if len(_cache) >= _CACHE_MAX_KEYS:
        _cache.clear()
    _cache[cache_key] = out
    return out
