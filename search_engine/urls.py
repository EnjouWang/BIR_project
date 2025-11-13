from . import views
from django.urls import path

# app_name = "search_engine"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_xml, name="upload_xml"),
    path("search/", views.search_result, name="search_results"),
    path("delete/<int:file_id>/", views.delete_file, name="delete_file"),
    path("zipf/", views.zipf_analysis, name="zipf_analysis"),
    path("train_model/", views.train_model, name="train_model"),
    path("word2vec/", views.word2vec_analysis, name="word2vec_analysis"),
]