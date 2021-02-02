'''
Created on 16 dic. 2020

@author: Manu
'''
#encoding:utf-8
from django import forms
from principal.models import Jugador, Ejercicio, ObjetivoTecnico,\
    ObjetivoTactico, Equipo, Partido, DetallesPartido, Entrenamiento, Cooper

class BusquedaEquipo(forms.Form):
    nombre = forms.CharField(label="Nombre", required=True)

class CrearPartido(forms.ModelForm):
    class Meta:
        model = Partido
        exclude = ['equipo']
        
class EditarJugador(forms.ModelForm):
    class Meta:
        model = Jugador
        exclude = ['nombre', 'apellidos', 'equipo']

class EditarInforme(forms.ModelForm):
    class Meta:
        model = DetallesPartido
        exclude = ['fecha', 'local', 'visitante', 'resultado', 'jugador', 'partido']

class CrearEntrenamiento(forms.ModelForm):
    class Meta:
        model = Entrenamiento
        exclude = ['equipo']

class CrearTestCooper(forms.ModelForm):
    class Meta:
        model = Cooper
        exclude = ['jugador']