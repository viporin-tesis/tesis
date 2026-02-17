from django.urls import path
from . import views

urlpatterns = [
    # Esto apunta a la función 'index' en views.py
    path('', views.index, name='index'),
]