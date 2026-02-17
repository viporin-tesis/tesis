from django.contrib import admin
from django.urls import path, include  # <--- FÍJATE AQUÍ: Agregamos 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('turismo.urls')), # <--- Y AQUÍ: Conectamos tu app
]