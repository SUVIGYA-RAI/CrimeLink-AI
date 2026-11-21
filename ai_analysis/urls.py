from django.urls import path
from . import views

app_name = 'ai_analysis'

urlpatterns = [
    # Dashboard
    path('',                                            views.home,                 name='home'),

    # Entity extraction
    path('extract/<int:file_id>/',                      views.extract_from_file,    name='extract_from_file'),
    path('entities/<int:file_id>/',                     views.entity_list,          name='entity_list'),
    path('entities/review/<int:entity_id>/<str:action>/', views.review_entity,      name='review_entity'),

    # Relationships
    path('relationships/',                              views.relationship_list,    name='relationship_list'),
    path('relationships/add/',                          views.add_relationship,     name='add_relationship'),
    path('relationships/review/<int:rel_id>/<str:action>/', views.review_relationship, name='review_relationship'),

    # Anomaly detection
    path('alerts/',                                     views.alert_list,           name='alert_list'),
    path('alerts/run/',                                 views.run_anomaly_detection,name='run_anomaly_detection'),
    path('alerts/review/<int:alert_id>/<str:action>/', views.review_alert,         name='review_alert'),
]
