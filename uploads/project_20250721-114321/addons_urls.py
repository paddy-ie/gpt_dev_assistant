from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.addons_dashboard, name='addons_dashboard'),
]