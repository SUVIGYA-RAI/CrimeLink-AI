"""
Entities app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'entities'

urlpatterns = [
    # Person URLs
    path('persons/', views.person_list, name='person_list'),
    path('persons/new/', views.person_create, name='person_create'),
    path('persons/<int:pk>/', views.person_detail, name='person_detail'),
    path('persons/<int:pk>/edit/', views.person_edit, name='person_edit'),
    path('persons/<int:pk>/delete/', views.person_delete, name='person_delete'),

    # Vehicle URLs
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/new/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),

    # Organization URLs
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/new/', views.organization_create, name='organization_create'),
    path('organizations/<int:pk>/', views.organization_detail, name='organization_detail'),
    path('organizations/<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.organization_delete, name='organization_delete'),

    # Location URLs
    path('locations/', views.location_list, name='location_list'),
    path('locations/new/', views.location_create, name='location_create'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('locations/<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),

    # Phone Record URLs
    path('phone-records/', views.phone_record_list, name='phone_record_list'),
    path('phone-records/new/', views.phone_record_create, name='phone_record_create'),
    path('phone-records/<int:pk>/', views.phone_record_detail, name='phone_record_detail'),
    path('phone-records/<int:pk>/edit/', views.phone_record_edit, name='phone_record_edit'),
    path('phone-records/<int:pk>/delete/', views.phone_record_delete, name='phone_record_delete'),
]
