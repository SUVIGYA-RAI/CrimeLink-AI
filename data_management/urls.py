from django.urls import path
from . import views

app_name = 'data_management'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload'),
    path('preview/<int:file_id>/', views.preview_csv, name='preview_csv'),
    path('import/<int:file_id>/', views.confirm_import_csv, name='confirm_import_csv'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('files/', views.file_list, name='file_list'),
]
