from principal.models import Posicion,Ejercicio,Entrenamiento,Partido,Jugador,Falta, Cooper,\
    ObjetivoTactico, ObjetivoTecnico, ObjetivoFisico, ObjetivoPsicologico, ObjetivoEspecifico, DetallesPartido, Equipo
from django.contrib import admin

# Register your models here.
admin.site.register(Posicion)
admin.site.register(Ejercicio)
admin.site.register(DetallesPartido)
admin.site.register(Equipo)
admin.site.register(Entrenamiento)
admin.site.register(Partido)
admin.site.register(Jugador)
admin.site.register(Cooper)
admin.site.register(Falta)
admin.site.register(ObjetivoTactico)
admin.site.register(ObjetivoTecnico)
admin.site.register(ObjetivoFisico)
admin.site.register(ObjetivoPsicologico)
admin.site.register(ObjetivoEspecifico)
