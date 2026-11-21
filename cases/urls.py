"""
Cases app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('new/', views.case_create, name='case_create'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    path('<int:pk>/edit/', views.case_edit, name='case_edit'),
    path('<int:pk>/delete/', views.case_delete, name='case_delete'),
    path('<int:pk>/link-entity/', views.case_link_entity, name='case_link_entity'),
    path('<int:pk>/unlink-entity/<str:entity_type>/<int:entity_id>/', views.case_unlink_entity, name='case_unlink_entity'),
]
