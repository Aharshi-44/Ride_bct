from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone

from .forms import BookRideForm
from .models import Ride, RideRejection
from .services import (
    BASE_FARE,
    PER_KM_RATE,
    PER_MIN_RATE,
    calculate_fare,
    maybe_advance_ride_status,
    route_metrics,
)


def _user_can_view_ride(user, ride):
    return ride.user_id == user.id or (ride.driver_id and ride.driver_id == user.id)


def _is_ajax_request(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@login_required
@require_http_methods(["GET", "POST"])
def book_ride(request):
    if request.user.is_driver:
        messages.warning(request, "Passenger accounts can book rides. Switch to a rider account.")
        return redirect("accounts:dashboard")

    fare_display = {
        "base_fare": BASE_FARE,
        "per_km_rate": PER_KM_RATE,
        "per_min_rate": PER_MIN_RATE,
    }

    preview_distance = None
    preview_fare = None
    preview_duration_min = None

    if request.method == "POST":
        form = BookRideForm(request.POST)
        action = request.POST.get("book_action", "confirm")

        if action == "preview":
            if form.is_valid():
                try:
                    p_lat = Decimal(form.cleaned_data["pickup_lat"])
                    p_lng = Decimal(form.cleaned_data["pickup_lng"])
                    d_lat = Decimal(form.cleaned_data["drop_lat"])
                    d_lng = Decimal(form.cleaned_data["drop_lng"])
                    dist_m, dur_s = route_metrics(p_lat, p_lng, d_lat, d_lng)
                    preview_distance = (Decimal(dist_m) / Decimal(1000)).quantize(Decimal("0.01"))
                    preview_duration_min = int((dur_s + 59) // 60)
                    preview_fare = calculate_fare(preview_distance, dur_s)
                except Exception as e:
                    messages.error(request, f"Could not fetch route data. Please try again. ({e})")
            else:
                messages.error(request, "Please enter valid pickup and drop locations.")
            return render(
                request,
                "rides/book.html",
                {
                    **fare_display,
                    "form": form,
                    "preview_distance": preview_distance,
                    "preview_fare": preview_fare,
                    "preview_duration_min": preview_duration_min,
                },
            )

        if action == "confirm" and not form.is_valid():
            if _is_ajax_request(request):
                return JsonResponse(
                    {"ok": False, "error": "validation", "errors": form.errors.get_json_data()},
                    status=400,
                )

        if form.is_valid():
            try:
                p_lat = Decimal(form.cleaned_data["pickup_lat"])
                p_lng = Decimal(form.cleaned_data["pickup_lng"])
                d_lat = Decimal(form.cleaned_data["drop_lat"])
                d_lng = Decimal(form.cleaned_data["drop_lng"])
                dist_m, dur_s = route_metrics(p_lat, p_lng, d_lat, d_lng)
                distance_km = (Decimal(dist_m) / Decimal(1000)).quantize(Decimal("0.01"))
                fare = calculate_fare(distance_km, dur_s)
            except Exception as e:
                if _is_ajax_request(request):
                    return JsonResponse({"ok": False, "error": str(e)}, status=400)
                messages.error(request, f"Could not fetch route data. Please try again. ({e})")
                return render(
                    request,
                    "rides/book.html",
                    {
                        **fare_display,
                        "form": form,
                        "preview_distance": preview_distance,
                        "preview_fare": preview_fare,
                        "preview_duration_min": preview_duration_min,
                    },
                )

            ride = Ride.objects.create(
                user=request.user,
                driver=None,
                pickup_location=form.cleaned_data["pickup_location"],
                drop_location=form.cleaned_data["drop_location"],
                pickup_place_id="",
                drop_place_id="",
                pickup_lat=p_lat,
                pickup_lng=p_lng,
                drop_lat=d_lat,
                drop_lng=d_lng,
                distance_meters=dist_m,
                duration_seconds=dur_s,
                status=Ride.Status.PENDING,
                fare=fare,
                distance_km=distance_km,
            )
            if _is_ajax_request(request):
                return JsonResponse({"ok": True, "ride_id": ride.pk})
            return redirect(f"{reverse('rides:book')}?wait={ride.pk}")
    else:
        form = BookRideForm()

    wait_ride_id = None
    w = request.GET.get("wait")
    if w and str(w).isdigit():
        wr = Ride.objects.filter(pk=int(w), user=request.user).first()
        if wr and wr.status == Ride.Status.PENDING:
            wait_ride_id = wr.pk

    return render(
        request,
        "rides/book.html",
        {
            **fare_display,
            "form": form,
            "preview_distance": preview_distance,
            "preview_fare": preview_fare,
            "preview_duration_min": preview_duration_min,
            "wait_ride_id": wait_ride_id,
        },
    )


@login_required
def payment_placeholder(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if ride.user_id != request.user.id:
        return HttpResponseForbidden()
    if ride.status == Ride.Status.CANCELLED:
        messages.error(request, "This ride was cancelled.")
        return redirect("accounts:dashboard")
    if ride.status == Ride.Status.PENDING:
        messages.info(request, "Your ride is still waiting for a driver.")
        return redirect(f"{reverse('rides:book')}?wait={ride.pk}")
    if ride.status != Ride.Status.ACCEPTED:
        return redirect("rides:ride_status", pk=ride.pk)
    if request.method == "POST":
        messages.success(request, "Payment successful! Your ride is confirmed.")
        return redirect("rides:ride_status", pk=ride.pk)
    return render(request, "rides/payment.html", {"ride": ride})


@login_required
def ride_status(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if not _user_can_view_ride(request.user, ride):
        return HttpResponseForbidden()
    ride = maybe_advance_ride_status(ride)
    driver_profile = None
    if ride.driver_id:
        driver_profile = getattr(ride.driver, "driver_profile", None)
    eta_min = None
    if ride.duration_seconds:
        eta_min = int((ride.duration_seconds + 59) // 60)
    can_driver_cancel = (
        request.user.is_driver
        and ride.driver_id == request.user.id
        and ride.status in (Ride.Status.ACCEPTED, Ride.Status.ONGOING)
    )
    return render(
        request,
        "rides/status.html",
        {
            "ride": ride,
            "driver_profile": driver_profile,
            "eta_min": eta_min,
            "can_driver_cancel": can_driver_cancel,
        },
    )


@login_required
def ride_status_api(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if not _user_can_view_ride(request.user, ride):
        return JsonResponse({"error": "forbidden"}, status=403)
    ride = maybe_advance_ride_status(ride)
    driver = ride.driver
    vehicle = ""
    if driver:
        dp = getattr(driver, "driver_profile", None)
        if dp:
            vehicle = dp.vehicle_number
    payload = {
        "id": ride.id,
        "status": ride.status,
        "fare": str(ride.fare),
        "pickup_location": ride.pickup_location,
        "drop_location": ride.drop_location,
        "driver_name": driver.get_full_name() or driver.username if driver else "",
        "vehicle_number": vehicle,
        "distance_km": str(ride.distance_km),
        "duration_seconds": ride.duration_seconds or 0,
    }
    return JsonResponse(payload)


@login_required
@require_http_methods(["POST"])
def toggle_driver_availability(request):
    if not request.user.is_driver:
        return HttpResponseForbidden()
    from accounts.models import DriverProfile

    profile = get_object_or_404(DriverProfile, user=request.user)
    profile.is_available = not profile.is_available
    profile.save(update_fields=["is_available"])
    state = "online" if profile.is_available else "offline"
    messages.info(request, f"You are now {state} for new assignments.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"is_available": profile.is_available})
    return redirect("accounts:dashboard")


@login_required
@require_http_methods(["POST"])
def accept_ride(request, pk: int):
    if not request.user.is_driver:
        return HttpResponseForbidden()

    with transaction.atomic():
        ride = (
            Ride.objects.select_for_update()
            .filter(pk=pk)
            .first()
        )
        if not ride:
            messages.warning(request, "Ride not found.")
            return redirect("accounts:dashboard")

        if ride.status != Ride.Status.PENDING or ride.driver_id is not None:
            messages.warning(request, "This ride is no longer available to accept.")
            return redirect("accounts:dashboard")

        updated = (
            Ride.objects.filter(pk=ride.pk, status=Ride.Status.PENDING, driver__isnull=True)
            .update(
                driver=request.user,
                status=Ride.Status.ACCEPTED,
                accepted_at=timezone.now(),
            )
        )
        if updated != 1:
            messages.warning(request, "This ride was accepted by another driver.")
            return redirect("accounts:dashboard")

    messages.success(request, "Ride accepted.")
    return redirect("rides:ride_status", pk=pk)


@login_required
@require_http_methods(["POST"])
def reject_ride(request, pk: int):
    if not request.user.is_driver:
        return HttpResponseForbidden()

    ride = get_object_or_404(Ride, pk=pk)
    if ride.status != Ride.Status.PENDING or ride.driver_id is not None:
        messages.warning(request, "This ride is no longer available to reject.")
        return redirect("accounts:dashboard")

    RideRejection.objects.get_or_create(ride=ride, driver=request.user)
    messages.info(request, "Ride rejected. It will no longer be shown to you.")
    return redirect("accounts:dashboard")


@login_required
@require_http_methods(["POST"])
def cancel_ride(request, pk: int):
    if not request.user.is_driver:
        return HttpResponseForbidden()

    ride = get_object_or_404(Ride, pk=pk)
    if ride.driver_id != request.user.id:
        return HttpResponseForbidden()
    if ride.status not in (Ride.Status.ACCEPTED, Ride.Status.ONGOING):
        messages.warning(request, "This ride cannot be cancelled.")
        return redirect("accounts:dashboard")

    ride.status = Ride.Status.CANCELLED
    ride.save(update_fields=["status"])
    messages.info(request, "Ride cancelled. The rider will see this on their trip status.")
    return redirect("accounts:dashboard")


@login_required
@require_http_methods(["POST"])
def rider_cancel_ride(request, pk: int):
    if request.user.is_driver:
        return HttpResponseForbidden()
    ride = get_object_or_404(Ride, pk=pk)
    if ride.user_id != request.user.id:
        return HttpResponseForbidden()
    if ride.status != Ride.Status.PENDING:
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "error": "not_pending"}, status=400)
        messages.warning(request, "This ride can no longer be cancelled here.")
        return redirect("rides:ride_status", pk=pk)

    ride.status = Ride.Status.CANCELLED
    ride.save(update_fields=["status"])
    if _is_ajax_request(request):
        return JsonResponse({"ok": True})
    messages.info(request, "Ride cancelled.")
    return redirect("rides:book")
