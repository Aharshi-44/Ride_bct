from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import DriverProfile, User

admin.site.site_header = "Velora Ride Admin"
admin.site.site_title = "Velora Admin"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_driver", "is_staff")
    list_filter = ("is_driver", "is_staff", "is_superuser")
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("is_driver",)}),)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2", "is_driver"),
            },
        ),
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_number", "is_available")
    list_filter = ("is_available",)
    search_fields = ("user__username", "vehicle_number")
