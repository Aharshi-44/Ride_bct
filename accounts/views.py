from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from rides.models import Ride

from .forms import CustomAuthenticationForm, DriverRegistrationForm, UserRegistrationForm


def home(request):
    return render(request, "home.html")


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True


def register_user_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome aboard! Your account is ready.")
            return redirect("accounts:dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register_user.html", {"form": form})


def register_driver_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = DriverRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Driver profile created. You can go online when ready.")
            return redirect("accounts:dashboard")
    else:
        form = DriverRegistrationForm()
    return render(request, "accounts/register_driver.html", {"form": form})


@login_required
def dashboard(request):
    user = request.user
    if user.is_driver:
        profile = getattr(user, "driver_profile", None)
        completed = Ride.objects.filter(driver=user, status=Ride.Status.COMPLETED)
        earnings = completed.aggregate(total=Sum("fare"))["total"] or 0
        recent = Ride.objects.filter(driver=user).order_by("-created_at")[:10]
        return render(
            request,
            "dashboard_driver.html",
            {
                "profile": profile,
                "earnings": earnings,
                "completed_count": completed.count(),
                "recent_rides": recent,
            },
        )

    rides = Ride.objects.filter(user=user).order_by("-created_at")[:20]
    completed = Ride.objects.filter(user=user, status=Ride.Status.COMPLETED)
    total_spent = completed.aggregate(total=Sum("fare"))["total"] or 0
    return render(
        request,
        "dashboard_user.html",
        {
            "rides": rides,
            "total_spent": total_spent,
            "completed_count": completed.count(),
        },
    )
