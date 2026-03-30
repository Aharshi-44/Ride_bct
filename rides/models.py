from decimal import Decimal

from django.conf import settings
from django.db import models


class Ride(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"

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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ride {self.pk} ({self.status})"
