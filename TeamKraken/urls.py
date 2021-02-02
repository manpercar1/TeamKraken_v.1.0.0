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
    path('<int:id_equipo>/jugadores/', principal_views.jugadoresList),
    path('<int:id_equipo>/jugadores/jugador/<int:id_jugador>', principal_views.jugadorDetails),
    path('<int:id_equipo>/jugadores/jugador/<int:id_jugador>/editar', principal_views.editarJugador),
    path('<int:id_equipo>/partidos/partido/<int:id_detalles_partido>/<int:id_jugador>/editar', principal_views.editarInforme),
    path('<int:id_equipo>/crearTestCooper/<int:id_jugador>', principal_views.crearTestCooper),
    path('<int:id_equipo>/partidos/', principal_views.calendario),
    path('<int:id_equipo>/crearPartido/', principal_views.crearPartido),
    path('<int:id_equipo>/partidos/partido/<int:id_partido>/<int:id_jugador>', principal_views.informePartido),
    path('<int:id_equipo>/partidos/partido/<int:id_partido>', principal_views.partidoDetails),
    path('<int:id_equipo>/entrenamientos/', principal_views.entrenamientosList),
    path('<int:id_equipo>/crearEntrenamiento/', principal_views.crearEntrenamiento),
    path('<int:id_equipo>/entrenamientos/entrenamiento/<int:id_entrenamiento>', principal_views.entrenamientoDetails),
    path('<int:id_equipo>/ejercicios/', principal_views.buscar_ejerciciosporfiltro),
    path('<int:id_equipo>/confirmacion/', principal_views.confirmacion),
    path('<int:id_equipo>/obtenerEjercicios/', principal_views.obtenerEjercicios),
    path('<int:id_equipo>/ejercicios/ejercicio/<int:id_ejercicio>', principal_views.ejercicioDetails),
    path('añadirEquipo/', principal_views.añadirEquipo),
    path('añadirEquipo/detallesEquipo/<int:codEquipo>', principal_views.detallesEquipo),
    path('seleccionarEquipo/', principal_views.seleccionarEquipo),
    path('<int:codEquipo>/guardar', principal_views.guardarEquipo),
    path('<int:id_equipo>/misEquipos/', principal_views.misEquipos),
    path('equipos/<int:id_equipo>', principal_views.miEquipo),
    path('<int:id_equipo>', principal_views.paginaPrincipalEquipo),
    path('media/<path>', static.serve, {'document_root':settings.MEDIA_ROOT,}),
    #Vistas de usuario
    path('', users_views.welcome),
    path('register/', users_views.register),
    path('login/', users_views.login),
    path('logout/', users_views.logout),
]
