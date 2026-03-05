from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.voice_upload, name='voice_upload'),
]