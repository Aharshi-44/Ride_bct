from django.urls import path

from . import views

app_name = "locations"

urlpatterns = [
    path("search/", views.location_search, name="search"),
]
