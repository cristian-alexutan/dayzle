"""Django admin for the GeoGuesser game app: a read-only view of regions and locations.

Daily games are made from random locations, so nothing here authors puzzles. Admins can
deactivate a bad location, recheck panoramas with Google and tune a region's scoring.
"""

from django.contrib import admin, messages

from . import services
from .exceptions import StreetViewError
from .models import Location, Region
from .selectors import last_used_dates


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "is_active", "is_default", "score_scale_m", "min_spacing_m"]
    # Changing the bounds would leave locations outside them, so they're fixed after creation.
    readonly_fields = ["key", "name", "south", "west", "north", "east", "is_default"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["panorama_id", "region", "is_active", "last_used", "last_checked_at"]
    list_filter = ["region", "is_active"]
    search_fields = ["panorama_id"]
    readonly_fields = ["region", "panorama_id", "latitude", "longitude", "last_checked_at"]
    actions = ["deactivate", "recheck"]

    def get_queryset(self, request):
        return last_used_dates().select_related("region")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(ordering="last_used", description="Last used")
    def last_used(self, obj):
        return obj.last_used

    @admin.action(description="Deactivate (no longer used in new games)")
    def deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} location(s).")

    @admin.action(description="Recheck panoramas with Google")
    def recheck(self, request, queryset):
        try:
            report = services.recheck_locations(queryset.select_related("region"))
        except StreetViewError as error:
            self.message_user(request, error.message, level=messages.ERROR)
            return
        self.message_user(request, f"Checked {report.checked} location(s).")
        if report.removed:
            removed = ", ".join(location.panorama_id for location in report.removed)
            self.message_user(
                request, f"Google removed these, now deactivated: {removed}", messages.WARNING
            )
        if report.outside:
            outside = ", ".join(location.panorama_id for location in report.outside)
            self.message_user(
                request, f"Moved outside the region, now deactivated: {outside}", messages.WARNING
            )
        if report.skipped:
            self.message_user(
                request,
                f"Skipped {report.skipped} after temporary Google errors; try again.",
                messages.WARNING,
            )
