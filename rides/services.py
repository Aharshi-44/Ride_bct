import hashlib
import json
import math
import os
import random
from decimal import Decimal
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from .models import Ride


BASE_FARE = Decimal("50.00")
PER_KM_RATE = Decimal("10.00")
PER_MIN_RATE = Decimal("2.00")


def simulated_distance_km(pickup: str, drop: str) -> Decimal:
    """Deterministic pseudo-distance from route strings (1–25 km)."""
    raw = f"{pickup.strip().lower()}|{drop.strip().lower()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    n = int(digest[:8], 16)
    km = 1 + (n % 250) / 10  # 1.0 .. 25.9
    return Decimal(str(round(km, 2)))


def simulated_pickup_distance_km(driver_area: str, pickup: str) -> Decimal:
    """Deterministic pseudo-distance from driver area to pickup (0.2–12.1 km)."""
    raw = f"{driver_area.strip().lower()}|{pickup.strip().lower()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    n = int(digest[:8], 16)
    km = 0.2 + (n % 120) / 10  # 0.2 .. 12.1
    return Decimal(str(round(km, 2)))


def random_distance_km() -> Decimal:
    """Alternative: random distance for demo variety."""
    return Decimal(str(round(random.uniform(2.0, 18.0), 2)))


def _billable_minutes(duration_seconds: int) -> int:
    """Whole minutes, rounded up from route duration (matches displayed ETA)."""
    if duration_seconds <= 0:
        return 0
    return int((duration_seconds + 59) // 60)


def calculate_fare(distance_km: Decimal, duration_seconds: int) -> Decimal:
    """
    fare = base_fare + (distance_km * per_km_rate) + (billable_minutes * per_min_rate)
    """
    km_part = distance_km * PER_KM_RATE
    mins = _billable_minutes(duration_seconds)
    time_part = Decimal(mins) * PER_MIN_RATE
    return (BASE_FARE + km_part + time_part).quantize(Decimal("0.01"))


def _haversine_meters(
    a_lat: Decimal, a_lng: Decimal, b_lat: Decimal, b_lng: Decimal
) -> float:
    r = 6371000.0
    p1 = math.radians(float(a_lat))
    p2 = math.radians(float(b_lat))
    dlat = math.radians(float(b_lat - a_lat))
    dlng = math.radians(float(b_lng - a_lng))
    s = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(s)))


def _approximate_route_from_coordinates(
    origin_lat: Decimal, origin_lng: Decimal, dest_lat: Decimal, dest_lng: Decimal
) -> tuple[int, int]:
    """
    When OSRM is unreachable: bee-line × road factor and ETA at ~30 km/h (demo estimate).
    """
    straight = _haversine_meters(origin_lat, origin_lng, dest_lat, dest_lng)
    road_factor = 1.35
    dist_m = max(int(straight * road_factor), 100)
    speed_m_s = 30 * 1000 / 3600
    dur_s = max(int(dist_m / speed_m_s), 60)
    return (dist_m, dur_s)


def _osrm_base_urls() -> list[str]:
    primary = (getattr(settings, "OSM_OSRM_BASE_URL", "") or "").strip().rstrip("/")
    out: list[str] = []
    if primary:
        out.append(primary)
    disable_pub = os.environ.get("OSM_DISABLE_PUBLIC_OSRM_FALLBACK", "0") == "1"
    pub = (os.environ.get("OSM_PUBLIC_OSRM_BASE_URL") or "https://router.project-osrm.org").strip().rstrip("/")
    if not disable_pub and pub and pub not in out:
        out.append(pub)
    return out


def _try_osrm_route(
    base: str,
    origin_lat: Decimal,
    origin_lng: Decimal,
    dest_lat: Decimal,
    dest_lng: Decimal,
    user_agent: str,
) -> Optional[tuple[int, int]]:
    base = base.rstrip("/")
    if not base:
        return None
    try:
        olat, olng = float(origin_lat), float(origin_lng)
        dlat, dlng = float(dest_lat), float(dest_lng)
        data = _http_json(
            f"{base}/route/v1/driving/{olng},{olat};{dlng},{dlat}",
            {
                "overview": "false",
                "alternatives": "false",
                "steps": "false",
            },
            user_agent,
        )
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        route = data["routes"][0]
        return (int(route["distance"]), int(route["duration"]))
    except Exception:
        return None


def _http_json(endpoint: str, params: dict, user_agent: str) -> dict:
    qs = urlencode(params)
    url = f"{endpoint}?{qs}"
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _nominatim_user_agent() -> str:
    return (getattr(settings, "OSM_HTTP_USER_AGENT", "") or "Quick-Go-rides/1.0").strip()


def route_metrics(origin_lat: Decimal, origin_lng: Decimal, dest_lat: Decimal, dest_lng: Decimal) -> tuple[int, int]:
    """
    Driving distance/duration via OSRM (local URL first, then optional public demo server),
    or a coordinate-based estimate if everything is unreachable (e.g. no local OSRM).
    Returns (distance_meters, duration_seconds).
    """
    ua = _nominatim_user_agent()
    for base in _osrm_base_urls():
        got = _try_osrm_route(base, origin_lat, origin_lng, dest_lat, dest_lng, ua)
        if got:
            return got

    if os.environ.get("OSM_DISABLE_ROUTE_FALLBACK", "0") == "1":
        raise RuntimeError(
            "Could not reach OSRM; set OSM_OSRM_BASE_URL or allow the route fallback."
        )

    return _approximate_route_from_coordinates(origin_lat, origin_lng, dest_lat, dest_lng)


def maybe_advance_ride_status(ride: Ride) -> Ride:
    """
    Simulate lifecycle: accepted → ongoing → completed based on elapsed time.

    `pending` remains pending until a driver accepts.
    """
    if ride.status in (Ride.Status.COMPLETED, Ride.Status.CANCELLED):
        return ride

    if ride.status == Ride.Status.PENDING:
        return ride

    anchor = ride.accepted_at or ride.created_at
    elapsed = (timezone.now() - anchor).total_seconds()

    new_status = ride.status
    if elapsed >= 8:
        new_status = Ride.Status.COMPLETED
    elif elapsed >= 4:
        new_status = Ride.Status.ONGOING

    if new_status != ride.status:
        ride.status = new_status
        ride.save(update_fields=["status"])

    return ride
