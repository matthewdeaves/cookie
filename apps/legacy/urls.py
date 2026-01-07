"""URL configuration for legacy frontend."""

from django.urls import path

from . import views

app_name = 'legacy'

urlpatterns = [
    path('', views.profile_selector, name='profile_selector'),
    path('home/', views.home, name='home'),
    path('search/', views.search, name='search'),
]
