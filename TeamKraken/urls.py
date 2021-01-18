"""teamkraken URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from principal import views as principal_views
from users import views as users_views
from django.urls import include
from django.views import static
from django.conf import settings

urlpatterns = [
    #Vistas de la aplicacion principal
    path('admin/', admin.site.urls),
    path('jugadores/', principal_views.jugadoresList, name='jugadores'),
    path('jugadores/jugador/<int:id_jugador>', principal_views.jugadorDetails),
    path('partidos/', users_views.welcome),
    path('partidos/partido/<int:id_partido>/<int:id_jugador>', principal_views.partidoDetails),
    path('entrenamientos/', principal_views.entrenamientosList, name='entrenamientos'),
    path('entrenamientos/entrenamiento/<int:id_entrenamiento>', principal_views.entrenamientoDetails),
    path('ejercicios/', principal_views.buscar_ejerciciosporfiltro, name='ejercicios'),
    path('ejercicios/ejercicio/<int:id_ejercicio>', principal_views.ejercicioDetails),
    path('añadirEquipo/', principal_views.añadirEquipo),
    path('media/<path>', static.serve, {'document_root':settings.MEDIA_ROOT,}),
    #Vistas de usuario
    path('', users_views.welcome),
    path('register/', users_views.register),
    path('login/', users_views.login),
    path('logout/', users_views.logout),
]
