#encoding:utf-8
from django.shortcuts import render, get_object_or_404, redirect
from principal.models import Jugador, Partido, TestCooper, Entrenamiento, Ejercicio
from django.conf import settings
from principal.forms import BusquedaEjercicios, BusquedaEquipo #, BusquedaPartidosPorJugador
from bs4 import BeautifulSoup
import urllib.request
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, ID
from whoosh.qparser import QueryParser

# Create your views here.
def añadirEquipo(request):
    if request.user.is_authenticated == False:
        return redirect('/login')

    formulario = BusquedaEquipo()
    resultado = None

    if request.method=='POST':
        formulario = BusquedaEquipo(request.POST)
        if formulario.is_valid():
            #PARTE DE BEAUTIFULSOUP formulario.cleaned_data['nombre']
            print("cagada jaja")
    print("no cagada")
    return render(request, 'principal/buscarEquipo.html', {'formulario':formulario, 'resultado':resultado})

def seleccionarEquipo(request):
    if request.user.is_authenticated == False:
        return redirect('/login')
    return render(request, 'principal/seleccionarEquipo.html')

def jugadoresList(request):
    if request.user.is_authenticated == False:
        return redirect('/login')
    jugadores = Jugador.objects.all()
    return render(request, 'principal/jugadores.html', {'jugadores': jugadores})

def jugadorDetails(request, id_jugador):
    if request.user.is_authenticated == False:
        return redirect('/login')
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    entrenamientos = Entrenamiento.objects.filter(jugadores=id_jugador)
    partidos = Partido.objects.filter(jugador=id_jugador)
    testCooper = TestCooper.objects.filter(jugador=id_jugador)
    #partidos
    #test de cooper
    return render(request, 'principal/jugadorDetails.html', {'jugador': jugador, 'entrenamientos': entrenamientos, 'partidos': partidos,
                                                    'testCoopers': testCooper})

def partidoDetails(request, id_partido, id_jugador):
    if request.user.is_authenticated == False:
        return redirect('/login')
    partido = get_object_or_404(Partido, pk=id_partido)
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    return render(request, 'principal/partidoDetails.html', {'partido': partido, 'jugador': jugador})

def entrenamientosList(request):
    if request.user.is_authenticated == False:
        return redirect('/login')
    entrenamientos = Entrenamiento.objects.all()
    return render(request, 'principal/entrenamientos.html', {'entrenamientos': entrenamientos})

def entrenamientoDetails(request, id_entrenamiento):
    if request.user.is_authenticated == False:
        return redirect('/login')
    entrenamiento = get_object_or_404(Entrenamiento, pk=id_entrenamiento)
    return render(request, 'principal/entrenamientoDetails.html', {'entrenamiento': entrenamiento})

def ejerciciosList(request):
    if request.user.is_authenticated == False:
        return redirect('/login')
    ejercicios = Ejercicio.objects.filter(user=request.user)
    return render(request, 'principal/ejercicios.html', {'ejercicios': ejercicios})

def ejercicioDetails(request, id_ejercicio):
    if request.user.is_authenticated == False:
        return redirect('/login')
    ejercicio = get_object_or_404(Ejercicio, pk=id_ejercicio)
    return render(request, 'principal/ejercicioDetails.html', {'ejercicio': ejercicio, 'MEDIA_URL':settings.MEDIA_URL})

#def buscar_partidosporjugador(request):
#    formulario = BusquedaPartidosPorJugador()
#    partidos = None
#    jugador = None
#    
#    if request.method=='POST':
#        formulario = BusquedaPartidosPorJugador(request.POST)      
#        if formulario.is_valid():
#            jugador=Jugador.objects.get(id=formulario.cleaned_data['jugador'])
#            partidos = jugador.partido_set.all()
#            
#    return render(request, 'partidos.html', {'formulario':formulario, 'partidos':partidos, 'jugador':jugador})

def buscar_ejerciciosporfiltro(request):
    if request.user.is_authenticated == False:
        return redirect('/login')
    formulario = BusquedaEjercicios()
    resultado = None
    
    if request.method=='POST':
        formulario = BusquedaEjercicios(request.POST)      
        if formulario.is_valid():
            resultado = Ejercicio.objects.filter(objetivoTecnico=formulario.cleaned_data['objTecnico'], 
                                                  objetivoTactico=formulario.cleaned_data['objTactico'])
    
    ejercicios = Ejercicio.objects.all()
    return render(request, 'principal/ejercicios.html', {'formulario':formulario, 'resultado':resultado, 'ejercicios': ejercicios})

#-------------PARTE DE WOOSH Y BEAUTIFULSOUP--------------

#PARA EL FORMULARIO DE BUSCAR EQUIPO:
#SE DEBE INTRODUCIR EN EL FORMULARIO SOLO EL NOMBRE. ACCEDER A ESTA URL AL ENVIAR https://www.rfaf.es/pnfg/NPcd/NFG_Clubes?cod_primaria=1000118&NPcd_Page=1&nueva_ventana=&Buscar=1&orden=&cod_club=&nclub=jorge+juan&Sch_CodCategoria=&cod_provincia=&localidad_txt=--+Seleccione+Provincia+--&localidad=0&code_delegacion=&cod_delegacion=&cod_postal=&NPcd_PageLines=20

def extraer_pagina_jornada(url):
    
    lista =[]
    
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f,"lxml")    
    l = s.find_all("div", class_= "center-content") #lista de partidos de la pagina
    for i in l:
        titulo = i.h2.a.string
        aux = i.find("div",class_="news-submitted")
        autor = aux.find_all("a")[1].string      
        fuentelink = aux.find("span",class_="showmytitle")
        if fuentelink:
            fuente = fuentelink.string
            link = fuentelink['title']
        else: #porque hay algunos casos que no tienen fuente y link
            fuente = "Anonima"
            link = "Desconocido"
        if aux.find("span",{'data-ts':True,'title':re.compile("publicado")}): 
            fecha_ts = aux.find("span",{'data-ts':True,'title':re.compile("publicado")})['data-ts']
        else: #porque hay algunos casos que no tienen fecha de publiacacion, solo de enviado
            fecha_ts = aux.find("span",{'data-ts':True,'title':re.compile("enviado")})['data-ts']
        fecha = datetime.fromtimestamp(int(fecha_ts))
        contenido = i.find("div",class_="news-content").get_text()
        lista.append((titulo,autor,fuente,link,fecha,contenido))
        
    return lista

def extraer_jornada(jornada):
    
    partido = extraer_pagina_jornada("http://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&"
                                    +"CodCompeticion=22839338&CodGrupo=22839345&CodTemporada=16&CodJornada="
                                    +str(jornada)+"&Sch_Codigo_Delegacion=&Sch_Tipo_Juego=")
        
    return partido

def calendarioPartidos(request):
    return render(request, "partidos.html")
#PARA CREAR UN ENTRENAMIENTO, A�ADIR "CREAR ENTRENAMIENTO" A LA VISTA DE EJERCICIOS.
#CUANDO SE CREE UN ENTRENAMIENTO QUE NO SE A�ADA NI JUGADORES NI FALTAS (PONER NULLABLE EN MODELO SI ES NECESARIO QUE AUN NO LO SE)
#PARA A�ADIR LISTA DE ASISTENCIA A LOS ENTRENAMIENTOS, A�ADIR BOTON "EDITAR ENTRENAMIENTO" EN LA VISTA DE DETALLES DE UN ENTRENAMIENTO
#PARA A�ADIR LAS FALTAS A LOS ENTRENAMIENTOS, PONER UN BOTON "A�ADIR FALTA"

#POSIBLE IDEA PARA LOS PARTIDOS:
#EN LA VISTA PARTIDOS, PONER UN BOTON QUE SEA A�ADIR NUEVO PARTIDO Y QUE MUESTRE UNA LISTA DE TODOS LOS JUGADORES. AL LADO DE CADA JUGADOR
#HABR� UN BOTON PARA A�ADIR A LA LISTA DE CONVOCADOS QUE LO QUE HAR� SER� CREAR UN PARTIDO VAC�O PARA CADA JUGADOR. DESPU�S DEL PARTIDO, HABR�
#QUE IR JUGADOR POR JUGADOR CAMBIANDO SUS ESTAD�STICAS DEL PARTIDO 

    