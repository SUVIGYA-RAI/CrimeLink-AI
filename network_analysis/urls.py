from django.urls import path
from . import views

app_name = 'network_analysis'

urlpatterns = [
    path('',               views.home,          name='home'),
    path('rebuild/',       views.rebuild_graph,  name='rebuild_graph'),
    path('graph/',         views.network_graph,  name='network_graph'),
]
