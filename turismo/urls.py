from django.urls import path
from django.contrib.auth import views as auth_views # <--- IMPORTANTE: Vistas de seguridad de Django
from . import views

urlpatterns = [
    path('', views.landing, name='landing'), # La nueva portada pública
    path('explorar/', views.index, name='index'), # El catálogo de lugares
    path('lugar/<int:lugar_id>/', views.detalle_lugar, name='detalle_lugar'),
    path('registro/', views.registro, name='registro'),
    
    # NUEVAS RUTAS: Iniciar y Cerrar Sesión
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # ... tus otras rutas ...
    path('registro/', views.registro, name='registro'),
    path('perfil/', views.perfil, name='perfil'), # <--- NUEVA RUTA

   
    
    # NUEVA RUTA PARA EL DASHBOARD MUNICIPAL
    path('dashboard/', views.dashboard_municipal, name='dashboard_municipal'),
]
