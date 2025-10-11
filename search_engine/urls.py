from . import views
from django.urls import path

# app_name = "search_engine"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_xml, name="upload_xml"),
    path("search/", views.search_result, name="search_results"),
    path("delete/<int:file_id>/", views.delete_file, name="delete_file"),
]