"""
Entities app admin configuration.
"""

from django.contrib import admin
from .models import Person, Vehicle, Organization, Location, PhoneRecord


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'age', 'gender', 'phone_number', 'date_added')
    search_fields = ('full_name', 'phone_number')
    list_filter = ('gender',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'vehicle_type', 'model_name', 'color', 'owner', 'date_added')
    search_fields = ('registration_number', 'model_name')
    list_filter = ('vehicle_type',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'city_from_address', 'date_added')
    search_fields = ('name',)
    list_filter = ('organization_type',)

    def city_from_address(self, obj):
        return obj.address[:50] if obj.address else '-'
    city_from_address.short_description = 'Address'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('location_name', 'city', 'state', 'date_added')
    search_fields = ('location_name', 'city')
    list_filter = ('state',)


@admin.register(PhoneRecord)
class PhoneRecordAdmin(admin.ModelAdmin):
    list_display = ('caller_number', 'receiver_number', 'call_date', 'call_time', 'duration', 'related_case')
    search_fields = ('caller_number', 'receiver_number')
    list_filter = ('call_date',)
