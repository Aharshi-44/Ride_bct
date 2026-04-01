from decimal import Decimal

from django.conf import settings
from django.db import models


class Ride(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rides_as_passenger",
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rides_as_driver",
    )
    pickup_location = models.CharField(max_length=255)
    drop_location = models.CharField(max_length=255)
    pickup_place_id = models.CharField(max_length=255, blank=True, default="")
    drop_place_id = models.CharField(max_length=255, blank=True, default="")
    pickup_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    pickup_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    drop_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    drop_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    distance_meters = models.IntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ride {self.pk} ({self.status})"


class RideRejection(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="rejections")
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ride_rejections",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ride", "driver"], name="uniq_ride_rejection_ride_driver"),
        ]

    def __str__(self):
        return f"RideRejection(ride={self.ride_id}, driver={self.driver_id})"
