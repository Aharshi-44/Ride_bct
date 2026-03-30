from django.contrib import admin

from .models import Ride


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "driver", "status", "fare", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("pickup_location", "drop_location", "user__username", "driver__username")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user", "driver")
