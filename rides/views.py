from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import DriverProfile

from .forms import BookRideForm
from .models import Ride
from .services import calculate_fare, maybe_advance_ride_status, simulated_distance_km


def _user_can_view_ride(user, ride):
    return ride.user_id == user.id or (ride.driver_id and ride.driver_id == user.id)


@login_required
@require_http_methods(["GET", "POST"])
def book_ride(request):
    if request.user.is_driver:
        messages.warning(request, "Passenger accounts can book rides. Switch to a rider account.")
        return redirect("accounts:dashboard")

    preview_distance = None
    preview_fare = None

    if request.method == "POST":
        form = BookRideForm(request.POST)
        action = request.POST.get("action", "confirm")

        if action == "preview":
            if form.is_valid():
                preview_distance = simulated_distance_km(
                    form.cleaned_data["pickup_location"],
                    form.cleaned_data["drop_location"],
                )
                preview_fare = calculate_fare(preview_distance)
            else:
                messages.error(request, "Please enter valid pickup and drop locations.")
            return render(
                request,
                "rides/book.html",
                {
                    "form": form,
                    "preview_distance": preview_distance,
                    "preview_fare": preview_fare,
                },
            )

        if form.is_valid():
            driver_profile = (
                DriverProfile.objects.filter(is_available=True, user__is_active=True)
                .select_related("user")
                .order_by("?")
                .first()
            )
            if not driver_profile:
                messages.error(
                    request,
                    "No drivers are available right now. Please try again in a few minutes.",
                )
                return render(
                    request,
                    "rides/book.html",
                    {
                        "form": form,
                        "preview_distance": preview_distance,
                        "preview_fare": preview_fare,
                    },
                )

            distance = simulated_distance_km(
                form.cleaned_data["pickup_location"],
                form.cleaned_data["drop_location"],
            )
            fare = calculate_fare(distance)
            ride = Ride.objects.create(
                user=request.user,
                driver=driver_profile.user,
                pickup_location=form.cleaned_data["pickup_location"],
                drop_location=form.cleaned_data["drop_location"],
                status=Ride.Status.PENDING,
                fare=fare,
                distance_km=distance,
            )
            messages.success(request, "Ride booked! A driver has been assigned.")
            return redirect("rides:payment", pk=ride.pk)
    else:
        form = BookRideForm()

    return render(
        request,
        "rides/book.html",
        {
            "form": form,
            "preview_distance": preview_distance,
            "preview_fare": preview_fare,
        },
    )


@login_required
def payment_placeholder(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if ride.user_id != request.user.id:
        return HttpResponseForbidden()
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
    return render(
        request,
        "rides/status.html",
        {
            "ride": ride,
            "driver_profile": driver_profile,
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
    }
    return JsonResponse(payload)


@login_required
@require_http_methods(["POST"])
def toggle_driver_availability(request):
    if not request.user.is_driver:
        return HttpResponseForbidden()
    profile = get_object_or_404(DriverProfile, user=request.user)
    profile.is_available = not profile.is_available
    profile.save(update_fields=["is_available"])
    state = "online" if profile.is_available else "offline"
    messages.info(request, f"You are now {state} for new assignments.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"is_available": profile.is_available})
    return redirect("accounts:dashboard")
