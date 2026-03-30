import hashlib
import random
from decimal import Decimal

from django.utils import timezone

from .models import Ride


BASE_FARE = Decimal("50.00")
PER_KM = Decimal("10.00")


def simulated_distance_km(pickup: str, drop: str) -> Decimal:
    """Deterministic pseudo-distance from route strings (1–25 km)."""
    raw = f"{pickup.strip().lower()}|{drop.strip().lower()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    n = int(digest[:8], 16)
    km = 1 + (n % 250) / 10  # 1.0 .. 25.9
    return Decimal(str(round(km, 2)))


def random_distance_km() -> Decimal:
    """Alternative: random distance for demo variety."""
    return Decimal(str(round(random.uniform(2.0, 18.0), 2)))


def calculate_fare(distance_km: Decimal) -> Decimal:
    return (BASE_FARE + distance_km * PER_KM).quantize(Decimal("0.01"))


def maybe_advance_ride_status(ride: Ride) -> Ride:
    """
    Simulate lifecycle: pending → accepted → ongoing → completed
    based on elapsed time since creation (works with 3s polling).
    """
    if ride.status == Ride.Status.COMPLETED:
        return ride

    elapsed = (timezone.now() - ride.created_at).total_seconds()

    new_status = ride.status
    if elapsed >= 12:
        new_status = Ride.Status.COMPLETED
    elif elapsed >= 8:
        new_status = Ride.Status.ONGOING
    elif elapsed >= 4:
        new_status = Ride.Status.ACCEPTED
    else:
        new_status = Ride.Status.PENDING

    if new_status != ride.status:
        ride.status = new_status
        ride.save(update_fields=["status"])

    return ride
