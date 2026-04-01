from django.urls import path

from . import views

app_name = "rides"

urlpatterns = [
    path("book/", views.book_ride, name="book"),
    path("<int:pk>/payment/", views.payment_placeholder, name="payment"),
    path("<int:pk>/status/", views.ride_status, name="ride_status"),
    path("<int:pk>/status/api/", views.ride_status_api, name="ride_status_api"),
    path("<int:pk>/accept/", views.accept_ride, name="accept"),
    path("<int:pk>/reject/", views.reject_ride, name="reject"),
    path("<int:pk>/cancel/", views.cancel_ride, name="cancel"),
    path("<int:pk>/rider-cancel/", views.rider_cancel_ride, name="rider_cancel"),
    path("driver/toggle-availability/", views.toggle_driver_availability, name="toggle_availability"),
]
