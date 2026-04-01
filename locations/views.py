from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services import get_location_from_nominatim


@login_required
@require_GET
def location_search(request):
    q = request.GET.get("q", "")
    results = get_location_from_nominatim(q)
    return JsonResponse({"results": results})
