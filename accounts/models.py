from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_driver = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class DriverProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )
    vehicle_number = models.CharField(max_length=32)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["vehicle_number"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.vehicle_number}"
