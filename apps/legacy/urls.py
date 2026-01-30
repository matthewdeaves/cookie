"""URL configuration for legacy frontend."""

from django.urls import path

from . import views

app_name = "legacy"

urlpatterns = [
    path("", views.profile_selector, name="profile_selector"),
    path("home/", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("settings/", views.settings, name="settings"),
    path("all-recipes/", views.all_recipes, name="all_recipes"),
    path("favorites/", views.favorites, name="favorites"),
    path("collections/", views.collections, name="collections"),
    path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("recipe/<int:recipe_id>/", views.recipe_detail, name="recipe_detail"),
    path("recipe/<int:recipe_id>/play/", views.play_mode, name="play_mode"),
]
