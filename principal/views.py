#encoding:utf-8
from django.shortcuts import render, get_object_or_404, redirect
from principal.models import Jugador, Partido, Entrenamiento, Ejercicio, Equipo, DetallesPartido, Cooper, ObjetivoTecnico, ObjetivoTactico, ObjetivoFisico, ObjetivoPsicologico, ObjetivoEspecifico, Falta
from django.conf import settings
from principal.forms import BusquedaEquipo, CrearPartido, EditarJugador, EditarInforme, CrearEntrenamiento, CrearTestCooper
from bs4 import BeautifulSoup
import urllib.request, http.cookiejar
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, AndGroup, OrGroup

from selenium import webdriver

import sys

sys.setrecursionlimit(10000)

# Create your views here.

#---------------------------------------WOOSH Y BEAUTIFULSOUP BUSCAR EQUIPOS--------------------------------------

def extraer_datos_pagina_equipo(url_pagina):

    lista =[]
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome('C:/Windows/chromedriver', chrome_options=options)

    driver.get(url_pagina)

    page_source = driver.page_source
    s = BeautifulSoup(page_source,"lxml")
    #
    #
    #
    #CUIDADO: SI SE USA ESTE METODO CONTINUAMENTE LA PÁGINA TE BLOQUEA
    #LO COMENTO PA NO DAR POR CULO Y QUE NO ME BLOQUEE LA FEDERACIÓN
    #
    #
    #
    #El sitio al que queremos acceder requiere la aceptación previa de Cookies. Por lo tanto, construimos
    #un OpenerDirector con la clase HTTPCookieProcesor para "esquivar" ese paso
    cj = http.cookiejar.CookieJar()
    f = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    #Ahora, podemos acceder a la url
    r = f.open(url_pagina)
    s = BeautifulSoup(r,"lxml")
    l = s.find_all("tr")

    if len(l) == 0:
        return redirect("/errorBS")

    for i in l:
        elementos = i.find_all("td")
        if len(elementos) == 0: #El primer tr que se va a encontrar es de la cabecera de la tabla, que no contiene td
            continue
        codigo = elementos[0].string
        nombre = elementos[2].find_all("a")[0].string
        urlEquipo = elementos[2].find_all("a")[0]['href']
        categoria = elementos[5].string
        
        lista.append((codigo,nombre,urlEquipo,categoria))
    
    return lista

def esquema_equipo(listaEquipos):
    
    #definimos el esquema de la información
    schem = Schema(codigo=TEXT(stored=True), nombre=KEYWORD(stored=True), urlEquipo=TEXT(stored=True), categoria=KEYWORD(stored=True))
    
    #si ya existe el directorio del índice, lo eliminamos
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")

    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al índice
    writer = ix.writer()

    for equipo in listaEquipos:
        #Ahora añadimos cada elemento de la lista de equipos obtenidos al índice que hemos creado
        writer.add_document(codigo=str(equipo[0]), nombre=str(equipo[1]), urlEquipo=str(equipo[2]),
            categoria=str(equipo[3]))

    writer.commit()

def añadirEquipo(request):
    if request.user.is_authenticated == False:
        return redirect('/login')

    formulario = BusquedaEquipo()
    resultado = None
    context = []

    if request.method=='POST':
        formulario = BusquedaEquipo(request.POST)
        if formulario.is_valid():
            #PARTE DE BEAUTIFULSOUP
            nombreEquipo = formulario.cleaned_data['nombre']
            nombreEquipo = nombreEquipo.replace(' ', '+') #Sustituimos los espacios en blanco si es un nombre compuesto por el caracter + que es lo que se utiliza en el navegador

            resultado = extraer_datos_pagina_equipo("https://www.rfaf.es/pnfg/NPcd/NFG_LstEquipos?" +
                "cod_primaria=1000119&nueva_ventana=&Buscar=1&orden=&Sch_Clave_Acceso_Club=&" +
                "Sch_Codigo_Club=&Sch_Codigo_Categoria=&Sch_Codigo_Delegacion=&Sch_Clave_Acceso_Campo=&" +
                "Campo=&Sch_Nombre_Equipo="+ str(nombreEquipo) +"&Sch_Categoria_Club=&Sch_Fecha_Inicio=&" +
                "Sch_Fecha_Fin=&NPcd_PageLines=20")
            
            #Guardamos los datos extraidos en un índice para posteriormente listarlos
            esquema_equipo(resultado)

            #Ahora abrimos el índice y mostramos todos los equipos indexados
            ix=open_dir("Index")
            #creamos un searcher en el í­ndice    
            with ix.searcher() as searcher:
                #se crea la consulta: buscamos en el campo "codigo" el código de club resultante de la búsqueda,
                #ya que todos los equipos encontrados pertenecen al mismo club siempre
                query = QueryParser("codigo", ix.schema).parse(str(resultado[0][0]))
                #llamamos a la función search del searcher, pasándole como parámetro la consulta creada
                diccionarios = searcher.search(query)
                #recorremos los diccionarios obtenidos con la búsqueda
                aux = {}
                for dic in diccionarios: 
                    cod = dic['codigo']
                    nom = dic['nombre']
                    url = dic['urlEquipo']
                    cat = dic['categoria']
                    
                    #Obtenemos el código de equipo, que son los últimos 6 caracteres de la url del equipo
                    equ = url[61] + url[62] + url[63] + url[64] + url[65] + url[66]

                    aux = {
                        'codigo':cod,
                        'nombre':nom,
                        'codEquipo':equ,
                        'categoria':cat
                    }

                    context.append(aux)

    return render(request, 'principal/buscarEquipo.html', {'formulario':formulario, 'resultado':resultado, 'context':context})

#---------------------------------------FIN WOOSH Y BEAUTIFULSOUP BUSCAR EQUIPO--------------------------------------

#-------------------------------WOOSH Y BEAUTIFULSOUP DETALLES DEL EQUIPO SELECCIONADO--------------------------------------

def extraer_datos_pagina_detalles_equipo(url, codEquipo):
    
    datos = []
    jugadores = []

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome('C:/Windows/chromedriver', chrome_options=options)

    driver.get(url)

    page_source = driver.page_source
    s = BeautifulSoup(page_source,"lxml")
    
    nombre = s.find_all("h2")[0].string

    correspondencia = s.find_all("div", {'style' : 'margin-top: 10px;'})[1].contents
    domicilio = correspondencia[5].contents[1]
    localidad = correspondencia[7].contents[1]
    provincia = correspondencia[9].contents[1]
    codPostal = correspondencia[11].contents[1]
    email = correspondencia[13].contents[1]

    tablaJugadores = s.find_all("table", class_="table table-striped table-hover listadolic")[0]
    listaJugadores = tablaJugadores.find_all("tr")
    
    for i in listaJugadores:
        elementos = i.find_all("td")
        if len(elementos) == 0: #El primer tr que se va a encontrar es de la cabecera de la tabla, que no contiene td
            continue
        
        for elemento in elementos:
            #sustituimos la coma que separa el nombre de los apellidos por un espacio
            jugador = elemento.h5.string.strip()
            jugadores.append(jugador)

    datos = [nombre, domicilio, localidad, provincia, codPostal, email, codEquipo, jugadores]

    return datos

def esquema_detalles_equipo(datos):
    
    #Vamos a crear dos esquemas, uno para los datos del equipo, y otro para los jugadores

    #ESQUEMA DE LOS DATOS DEL EQUIPO
    schem = Schema(codEquipo=TEXT(stored=True), nombre=KEYWORD(stored=True), domicilio=KEYWORD(stored=True), 
                localidad=TEXT(stored=True), provincia=TEXT(stored=True), codPostal=TEXT(stored=True), 
                    email=TEXT(stored=True), key=TEXT(stored=True))
    
    if os.path.exists("Index_equipo"):
        shutil.rmtree("Index_equipo")
    os.mkdir("Index_equipo")

    ix = create_in("Index_equipo", schema=schem)
    writer = ix.writer()

    writer.add_document(codEquipo=str(datos[6]), nombre=str(datos[0]), domicilio=str(datos[1]), localidad=str(datos[2]), provincia=str(datos[3]),
        codPostal=str(datos[4]), email=str(datos[5]), key="equipo")

    writer.commit()

    #ESQUEMA DE LOS JUGADORES
    #El nombre es KEYWORD porque puede ser un nombre compuesto
    schemJugadores = Schema(nombre=KEYWORD(stored=True), apellidos=KEYWORD(stored=True), equipo=TEXT(stored=True))

    jugadores = datos[7]

    nombre = ""
    apellidos = ""

    if os.path.exists("Index_jugadores"):
        shutil.rmtree("Index_jugadores")
    os.mkdir("Index_jugadores")

    ix = create_in("Index_jugadores", schema=schemJugadores)
    writerJugadores = ix.writer()

    for jugador in jugadores:
        jugadorApellidosNombre = jugador.split(",")
        nombre = jugadorApellidosNombre[1]
        apellidos = jugadorApellidosNombre[0]
        writerJugadores.add_document(nombre=str(nombre), apellidos=str(apellidos), equipo=str(datos[6]))

    writerJugadores.commit()


def detallesEquipo(request, codEquipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    datos = extraer_datos_pagina_detalles_equipo("https://www.rfaf.es/pnfg/NPcd/NFG_VisEquipos?cod_primaria=1000119&Codigo_Equipo=" + str(codEquipo), codEquipo)

    #luego se guardará la información de "resultado" en OTRO índice
    esquema_detalles_equipo(datos)

    #Volvemos a abrir el índice del método anterior porque algunos datos vamos a mostrarlos también aquí
    ix=open_dir("Index")

    with ix.searcher() as searcher:
        #esta vez, filtramos por el nombre
        query = QueryParser("nombre", ix.schema).parse(str(datos[0]))
        diccionarios = searcher.search(query, limit=1)
        dic = diccionarios[0]
        aux = {}

        cod = dic['codigo']
        cat = dic['categoria']

        aux = {
            'codigo':cod,
            'categoria':cat
        }

    #Ahora obtenemos los datos del esquema del equipo
    ix_equipo = open_dir("Index_equipo")

    with ix_equipo.searcher() as searcherEquipo:
        query = QueryParser("codEquipo", ix_equipo.schema).parse(str(codEquipo))
        dicEquipo = searcherEquipo.search(query, limit=1)
        equipo = dicEquipo[0]

        auxEquipo = {
            'codigoEquipo':equipo['codEquipo'],
            'nombre':equipo['nombre'],
            'domicilio':equipo['domicilio'],
            'localidad':equipo['localidad'],
            'provincia':equipo['provincia'],
            'codPostal':equipo['codPostal'],
            'email':equipo['email'],
        }
        
    aux.update(auxEquipo)

    #Y ahora obtenemos los datos del esquema de los jugadores
    ix_jugadores = open_dir("Index_jugadores")
    jugadores = []

    with ix_jugadores.searcher() as searcherJugadores:
        query = QueryParser("equipo", ix_jugadores.schema).parse(str(codEquipo))
        #ponemos límite None para que nos devuelva todos los resultados
        diccionariosJugadores = searcherJugadores.search(query, limit=None)
        auxJugadores = {}

        for dicJugadores in diccionariosJugadores:
            nombre = dicJugadores['nombre']
            apellidos = dicJugadores['apellidos']

            auxJugadores = {
                'nombre':nombre,
                'apellidos':apellidos
            }

            jugadores.append(auxJugadores)

    return render(request, 'principal/detallesEquipo.html', {'context':aux, 'jugadores':jugadores})

def guardarEquipo(request, codEquipo):

    #Accedemos al índice del equipo y de los jugadores para obtener los datos que queremos guardar
    ix_equipo = open_dir("Index_equipo")

    with ix_equipo.searcher() as searcherEquipo:
        query = QueryParser("codEquipo", ix_equipo.schema).parse(str(codEquipo))
        dicEquipo = searcherEquipo.search(query, limit=1)
        equipo = dicEquipo[0]

        nombreEquipo = equipo['nombre']
        codigoEquipo = equipo['codEquipo']
        domicilioEquipo = equipo['domicilio']
        codigoPostalEquipo = equipo['codPostal']
        localidadEquipo = equipo['localidad']
        provinciaEquipo = equipo['provincia']
        emailEquipo = equipo['email']

    ix=open_dir("Index")

    with ix.searcher() as searcher:
        #esta vez, filtramos por el nombre
        query = QueryParser("nombre", ix.schema).parse(str(nombreEquipo))
        diccionarios = searcher.search(query, limit=1)
        dic = diccionarios[0]

        cat = dic['categoria']

    eq = Equipo(nombre=str(nombreEquipo), codigo=str(codigoEquipo), domicilio=str(domicilioEquipo), 
            codigoPostal=str(codigoPostalEquipo), localidad=str(localidadEquipo), provincia=str(provinciaEquipo),
            categoria=str(cat), email=str(emailEquipo), user=request.user)

    eq.save()

    ix_jugadores = open_dir("Index_jugadores")
    jugadores = []

    with ix_jugadores.searcher() as searcherJugadores:
        query = QueryParser("equipo", ix_jugadores.schema).parse(str(codEquipo))
        #ponemos límite None para que nos devuelva todos los resultados
        diccionariosJugadores = searcherJugadores.search(query, limit=None)
        auxJugadores = {}

        for dicJugadores in diccionariosJugadores:
            nombre = dicJugadores['nombre']
            apellidos = dicJugadores['apellidos']

            jugador = Jugador(nombre=str(nombre), apellidos=str(apellidos), equipo=eq)
            jugador.save()

    return render(request, 'principal/success.html')

#-------------------------------FIN WOOSH Y BEAUTIFULSOUP DETALLES DEL EQUIPO SELECCIONADO--------------------------------------

def misEquipos(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    equipos = Equipo.objects.filter(user=request.user)

    return render(request, 'principal/misEquipos.html', {'equipos':equipos, 'eq':eq})

def miEquipo(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    equipo = get_object_or_404(Equipo, pk=id_equipo)
    jugadores = Jugador.objects.filter(equipo=id_equipo)

    return render(request, 'principal/miEquipo.html', {'jugadores':jugadores, 'equipo':equipo, 'eq':equipo})

def seleccionarEquipo(request):
    if request.user.is_authenticated == False:
        return redirect('/login')

    if request.method=="POST":
        id_equipo=request.POST['equipos']
        return redirect("/" + str(id_equipo))
    
    equipos = Equipo.objects.filter(user=request.user)

    return render(request, 'principal/inicioEquipoSeleccionado.html', {'equipos':equipos})

def paginaPrincipalEquipo(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    equipos = Equipo.objects.filter(user=request.user)

    return render(request, 'principal/inicioEquipoSeleccionado.html', {'equipos':equipos, 'eq':eq})

def calendario(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')
    
    eq = get_object_or_404(Equipo, pk=id_equipo)
    partidos = Partido.objects.filter(equipo=eq)
    jugadores = Jugador.objects.filter(equipo=id_equipo)
    jugador = None

    if request.method=="POST":
        id_jugador=request.POST['jugadores']
        #ESTO SE PUEDE HACER CON WHOOSH TAMBIEN
        jugador = get_object_or_404(Jugador, pk=id_jugador)
        partidos = Partido.objects.filter(convocados=id_jugador)

    return render(request, 'principal/calendario.html', {'partidos':partidos, 'jugadores':jugadores,
        'p':jugador, 'eq':eq})

def crearPartido(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    formulario = CrearPartido()
    eq = get_object_or_404(Equipo, pk=id_equipo)

    if request.method=="POST":

        formulario = CrearPartido(request.POST)

        if formulario.is_valid():
            fecha = formulario.cleaned_data['fecha']
            local = formulario.cleaned_data['local']
            visitante = formulario.cleaned_data['visitante']
            resultado = formulario.cleaned_data['resultado']
            convocados = formulario.cleaned_data['convocados']
            equipo = formulario.cleaned_data['equipo']

            partido = Partido.objects.create(fecha=fecha, local=local, visitante=visitante, resultado=resultado,
                        equipo=equipo)
            
            partido.convocados.set(convocados)
            
            for jugador in convocados:
                detallesPartido = DetallesPartido.objects.create(fecha=fecha, local=local, visitante=visitante,
                        resultado=resultado, titular="No especificado", posicion=None, tirosPuerta=0, goles=0,
                        asistencias=0, robosBalon=0, balonesPerdidos=0, minutosJugados=0, amarillas=0, rojas=0,
                        jugador=jugador, partido=partido)

            return redirect('/' + str(id_equipo) + '/partidos')

    return render(request, 'principal/crearPartido.html', {'formulario': formulario, 'eq':eq})

def jugadoresList(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    schemJugadores = Schema(id=NUMERIC(int, stored=True), nombre=KEYWORD(stored=True), apellidos=KEYWORD(stored=True), posicion=KEYWORD(stored=True), equipo=TEXT(stored=True))

    eq = get_object_or_404(Equipo, pk=id_equipo)
    jugadores = Jugador.objects.filter(equipo=id_equipo)

    if os.path.exists("Index_jugadores"):
        shutil.rmtree("Index_jugadores")
    os.mkdir("Index_jugadores")

    ix = create_in("Index_jugadores", schema=schemJugadores)
    writerJugadores = ix.writer()

    for jugador in jugadores:
        writerJugadores.add_document(id=int(jugador.id), nombre=str(jugador.nombre), apellidos=str(jugador.apellidos), 
            posicion=str(jugador.posicionPrincipal), equipo=str(jugador.equipo))

    writerJugadores.commit()

    if request.method == 'POST':
        posicion = request.POST['posicion']
        ix_jugadores = open_dir("Index_jugadores")
        jugadores = []

        with ix_jugadores.searcher() as searcherJugadores:
            consulta = str(posicion) + " " + str(eq)
            query = MultifieldParser(["posicion","equipo"], ix_jugadores.schema, group=AndGroup).parse(str(consulta))
            #ponemos límite None para que nos devuelva todos los resultados
            diccionariosJugadores = searcherJugadores.search(query, limit=None)
            auxJugadores = {}

            for dicJugadores in diccionariosJugadores:
                auxJugadores = {
                    'id' : dicJugadores['id'],
                    'nombre' : dicJugadores['nombre'],
                    'apellidos' : dicJugadores['apellidos'],
                    'posicionPrincipal' : dicJugadores['posicion']
                }

                jugadores.append(auxJugadores)

    return render(request, 'principal/jugadores.html', {'jugadores': jugadores, 'eq': eq})

def jugadorDetails(request, id_jugador, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    entrenamientos = Entrenamiento.objects.filter(jugadores=id_jugador)
    detallesPartidos = DetallesPartido.objects.filter(jugador=id_jugador)
    testCoopers = Cooper.objects.filter(jugador=id_jugador)
    faltas = Falta.objects.filter(jugador=id_jugador)

    return render(request, 'principal/jugadorDetails.html', {'jugador': jugador, 'entrenamientos': entrenamientos,
        'partidos': detallesPartidos, 'testCoopers': testCoopers , 'faltas':faltas, 'eq':eq})

def editarJugador(request, id_equipo, id_jugador):
    if request.user.is_authenticated == False:
        return redirect('/login')
    
    formulario = EditarJugador()
    eq = get_object_or_404(Equipo, pk=id_equipo)

    if request.method == 'POST':

        formulario = EditarJugador(request.POST)

        if formulario.is_valid():
            
            jugador = get_object_or_404(Jugador, pk=id_jugador)
            
            jugador.fechaNacimiento = formulario.cleaned_data['fechaNacimiento']
            jugador.posicionPrincipal = formulario.cleaned_data['posicionPrincipal']
            jugador.altura = formulario.cleaned_data['altura']
            jugador.pieDominante = formulario.cleaned_data['pieDominante']
            ps = formulario.cleaned_data['posicionesSecundarias']
            jugador.posicionesSecundarias.set(ps)

            jugador.save(update_fields=['fechaNacimiento', 'posicionPrincipal', 'altura', 'pieDominante'])

            return redirect('/' + str(id_equipo) + '/jugadores/jugador/' + str(id_jugador))

    return render(request, 'principal/editarJugador.html', {'formulario': formulario, 'eq':eq})

def crearTestCooper(request, id_equipo, id_jugador):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    formulario = CrearTestCooper()

    if request.method == 'POST':
        formulario = CrearTestCooper(request.POST)
        if formulario.is_valid():
            fecha = formulario.cleaned_data['fecha']
            distancia = formulario.cleaned_data['distancia']
            vo2max = formulario.cleaned_data['vo2max']

            Cooper.objects.create(fecha=fecha, distancia=distancia, vo2max=vo2max, jugador=jugador)

            return redirect('/' + str(id_equipo) + '/jugadores/jugador/' + str(id_jugador))

    return render(request, 'principal/crearTestCooper.html', {'formulario': formulario, 'eq':eq})

def partidoDetails(request, id_partido, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    partido = get_object_or_404(Partido, pk=id_partido)

    return render(request, 'principal/partidoDetails.html', {'partido': partido, 'eq':eq})

def informePartido(request, id_partido, id_jugador, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    partido = DetallesPartido.objects.filter(jugador=id_jugador).filter(partido=id_partido)
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    return render(request, 'principal/informePartido.html', {'partido': partido[0], 'jugador': jugador, 'eq':eq})

def editarInforme(request, id_equipo, id_detalles_partido, id_jugador):
    if request.user.is_authenticated == False:
        return redirect('/login')
    
    eq = get_object_or_404(Equipo, pk=id_equipo)
    jugador = get_object_or_404(Jugador, pk=id_jugador)
    partido = get_object_or_404(DetallesPartido, pk=id_detalles_partido)
    formulario = EditarInforme()

    if request.method == 'POST':

        formulario = EditarInforme(request.POST)

        if formulario.is_valid():

            informe = get_object_or_404(DetallesPartido, pk=id_detalles_partido)

            informe.titular = formulario.cleaned_data['titular']
            informe.posicion = formulario.cleaned_data['posicion']
            informe.tirosPuerta = formulario.cleaned_data['tirosPuerta']
            informe.goles = formulario.cleaned_data['goles']
            informe.asistencias = formulario.cleaned_data['asistencias']
            informe.robosBalon = formulario.cleaned_data['robosBalon']
            informe.balonesPerdidos = formulario.cleaned_data['balonesPerdidos']
            informe.minutosJugados = formulario.cleaned_data['minutosJugados']
            informe.amarillas = formulario.cleaned_data['amarillas']
            informe.rojas = formulario.cleaned_data['rojas']
            
            informe.save(update_fields=['titular', 'posicion', 'tirosPuerta', 'goles', 'asistencias',
                'robosBalon', 'balonesPerdidos', 'minutosJugados', 'amarillas', 'rojas'])

            return redirect('/' + str(id_equipo) + '/partidos/partido/' + str(informe.partido.id) + '/' + str(id_jugador))

    return render(request, 'principal/editarInforme.html', {'formulario': formulario, 'eq':eq, 'jugador':jugador, 'partido':partido})

def entrenamientosList(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    entrenamientos = Entrenamiento.objects.filter(equipo=id_equipo)
    return render(request, 'principal/entrenamientos.html', {'entrenamientos': entrenamientos, 'eq':eq})

def crearEntrenamiento(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    formulario = CrearEntrenamiento()
    eq = get_object_or_404(Equipo, pk=id_equipo)

    if request.method=="POST":

        formulario = CrearEntrenamiento(request.POST)

        if formulario.is_valid():
            fecha = formulario.cleaned_data['fecha']
            ejercicios = formulario.cleaned_data['ejercicios']
            asistentes = formulario.cleaned_data['jugadores']

            entrenamiento = Entrenamiento.objects.create(fecha=fecha, equipo=eq)
            
            entrenamiento.ejercicios.set(ejercicios)
            entrenamiento.jugadores.set(asistentes)
            
            jugadores = Jugador.objects.filter(equipo=id_equipo)

            for jugador in jugadores:
                if jugador not in asistentes:
                    falta = Falta.objects.create(fecha=fecha, entrenamiento=entrenamiento, jugador=jugador)

            return redirect('/' + str(id_equipo) + '/entrenamientos')

    return render(request, 'principal/crearEntrenamiento.html', {'formulario': formulario, 'eq':eq})

def entrenamientoDetails(request, id_entrenamiento, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    entrenamiento = get_object_or_404(Entrenamiento, pk=id_entrenamiento)
    faltas = Falta.objects.filter(entrenamiento=id_entrenamiento)
    return render(request, 'principal/entrenamientoDetails.html', {'entrenamiento': entrenamiento, 'eq':eq, 'faltas':faltas})

#------------------------------PARTE DE WHOOSH Y BEAUTIFULSOUP DE LOS EJERCICIOS--------------------------------

def ejerciciosList(request, id_equipo):
    #AQUI SE LLAMA A CARGAR EL SISTEMA DE RECOMENDACIÓN
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    ejercicios = Ejercicio.objects.filter(user=request.user)
    return render(request, 'principal/ejercicios.html', {'ejercicios': ejercicios, 'eq':eq})

def extraer_ejercicios(url):

    lista = []

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome('C:/Windows/chromedriver', chrome_options=options)

    driver.get(url)

    page_source = driver.page_source
    s = BeautifulSoup(page_source,"lxml")
    l = s.find_all("div", class_="title")
    
    for e in l:
        objetivos_especificos = ['Objetivos especificos']
        objetivos_fisicos = ['Objetivos fisicos']
        objetivos_psicologicos = ['Objetivos psicologicos']
        objetivos_tacticos = ['Objetivos tacticos']
        objetivos_tecnicos = ['Objetivos tecnicos']
        driver.get("http://entrenamientosdefutbol.es/"+e.a['href'])
        page_source = driver.page_source
        ej = BeautifulSoup(page_source,"lxml")
        nombre = ej.find("h1").string
        aux = ej.find("h1").find_next_sibling("p").contents
        descripcion = ""
        i = 0
        for d in aux:
            if i == 0 or i % 2 == 0:
                descripcion = descripcion + str(d) + ". "
            i = i + 1
        div_contents = ej.find_all("div", class_="content")
        #MATERIALES
        div_materiales = div_contents[1]
        lista_materiales = div_materiales.find_all("li")
        materiales = ""
        for material in lista_materiales:
            if len(material.contents) > 1:
                materiales = materiales + "Dimensiones del campo:" + str(material.contents[1])
            else:
                materiales = materiales + str(material.string) + " | " 
        #CONSEJOS
        div_consejos = div_contents[2]
        lista_consejos = div_consejos.find_all("li")
        consejos = ""
        i = 0
        for consejo in lista_consejos:
            aux = str(consejo.contents[4])
            aux2 = aux.replace(": ", "").replace(".", "")
            if i == (len(lista_consejos) - 1):
                consejos = consejos + str(aux2)
            else:
                consejos = consejos + str(aux2) + " | "
            i = i + 1
        #OBJETIVOS
        div_objetivos = div_contents[3]
        h4_objetivos = div_objetivos.find_all("h4", class_="panel-title")
        for h4 in h4_objetivos:
            if h4.string == "Objetivos Específicos":
                parent = h4.parent
                vecino = parent.find_next_sibling("div")
                li_objetivos = vecino.find_all("li")
                for li in li_objetivos:
                    objetivo_especifico = li.a.string
                    objetivos_especificos.append(objetivo_especifico)
            elif h4.string == "Objetivos Físicos":
                parent = h4.parent
                vecino = parent.find_next_sibling("div")
                li_objetivos = vecino.find_all("li")
                for li in li_objetivos:
                    objetivo_fisico = li.a.string
                    objetivos_fisicos.append(objetivo_fisico)
            elif h4.string == "Objetivos Psicológicos":
                parent = h4.parent
                vecino = parent.find_next_sibling("div")
                li_objetivos = vecino.find_all("li")
                for li in li_objetivos:
                    objetivo_psicologico = li.a.string
                    objetivos_psicologicos.append(objetivo_psicologico)
            elif h4.string == "Objetivos Tácticos":
                parent = h4.parent
                vecino = parent.find_next_sibling("div")
                li_objetivos = vecino.find_all("li")
                for li in li_objetivos:
                    objetivo_tactico = li.a.string
                    objetivos_tacticos.append(objetivo_tactico)
            elif h4.string == "Objetivos Técnicos":
                parent = h4.parent
                vecino = parent.find_next_sibling("div")
                li_objetivos = vecino.find_all("li")
                for li in li_objetivos:
                    objetivo_tecnico = li.a.string
                    objetivos_tecnicos.append(objetivo_tecnico)

        lista.append((nombre, descripcion, materiales, consejos, objetivos_especificos, objetivos_fisicos,
            objetivos_psicologicos, objetivos_tacticos, objetivos_tecnicos))

    return lista

def esquema_ejercicios(request, ejercicios):

    schem = Schema(nombre=TEXT(stored=True), material=TEXT(stored=True), descripcion=TEXT(stored=True), 
                consejos=TEXT(stored=True), obj_fisicos=KEYWORD(stored=True, commas=True),
                obj_especificos=KEYWORD(stored=True, commas=True), obj_psicologicos=KEYWORD(stored=True, commas=True),
                obj_tecnicos=KEYWORD(stored=True, commas=True), obj_tacticos=KEYWORD(stored=True, commas=True),
                usuario=TEXT(stored=True))
    
    if os.path.exists("Index_ejercicios"):
        shutil.rmtree("Index_ejercicios")
    os.mkdir("Index_ejercicios")

    ix = create_in("Index_ejercicios", schema=schem)
    writer = ix.writer()

    for ejercicio in ejercicios:
        i=0
        #para el esquema
        objetivos_especificos = ""
        objetivos_fisicos = ""
        objetivos_psicolocigos = ""
        objetivos_tecnicos = ""
        objetivos_tacticos = ""
        #para el modelo
        objsE = []
        objsF = []
        objsP = []
        objsTa = []
        objsTe = []
        for e in ejercicio:
            if i == 0 or i == 1 or i == 2 or i == 3:
                i = i + 1
                continue
            if e[0] == 'Objetivos especificos':
                #eliminamos el primer elemento que era identificativo y convertimos la lista en cadena
                #para guardarla en el esquema de los ejercicios
                e.remove('Objetivos especificos')
                objetivos_especificos = ", ".join(e)
                #ahora recorremos la lista para comprobar si existen en la base de datos asociada al usuario,
                #si no existen, los guardamos
                for objetivo in e:
                    busqueda = ObjetivoEspecifico.objects.filter(nombre=objetivo).filter(user=request.user)
                    if len(busqueda) == 0:
                        obj = ObjetivoEspecifico.objects.create(nombre=objetivo, user=request.user)
                        objsE.append(obj)
                    else:
                        objsE.extend(busqueda)
            elif e[0] == 'Objetivos fisicos':
                e.remove('Objetivos fisicos')
                objetivos_fisicos = ", ".join(e)
                for objetivo in e:
                    busqueda = ObjetivoFisico.objects.filter(nombre=objetivo).filter(user=request.user)
                    if len(busqueda) == 0:
                        obj = ObjetivoFisico.objects.create(nombre=objetivo, user=request.user)
                        objsF.append(obj)
                    else:
                        objsF.extend(busqueda)
            elif e[0] == 'Objetivos psicologicos':
                e.remove('Objetivos psicologicos')
                objetivos_psicolocigos = ", ".join(e)
                for objetivo in e:
                    busqueda = ObjetivoPsicologico.objects.filter(nombre=objetivo).filter(user=request.user)
                    if len(busqueda) == 0:
                        obj = ObjetivoPsicologico.objects.create(nombre=objetivo, user=request.user)
                        objsP.append(obj)
                    else:
                        objsP.extend(busqueda)
            elif e[0] == 'Objetivos tecnicos':
                e.remove('Objetivos tecnicos')
                objetivos_tecnicos = ", ".join(e)
                for objetivo in e:
                    busqueda = ObjetivoTecnico.objects.filter(nombre=objetivo).filter(user=request.user)
                    if len(busqueda) == 0:
                        obj = ObjetivoTecnico.objects.create(nombre=objetivo, user=request.user)
                        objsTe.append(obj)
                    else:
                        objsTe.extend(busqueda)
            elif e[0] == 'Objetivos tacticos':
                e.remove('Objetivos tacticos')
                objetivos_tacticos = ", ".join(e)
                for objetivo in e:
                    busqueda = ObjetivoTactico.objects.filter(nombre=objetivo).filter(user=request.user)
                    if len(busqueda) == 0:
                        obj = ObjetivoTactico.objects.create(nombre=objetivo, user=request.user)
                        objsTa.append(obj)
                    else:
                        objsTa.extend(busqueda)
            i = i + 1
        
        #añadimos los datos al esquema
        writer.add_document(nombre=ejercicio[0], descripcion=ejercicio[1], material=ejercicio[2],
            consejos=ejercicio[3], obj_fisicos=objetivos_fisicos, obj_especificos=objetivos_especificos,
            obj_psicologicos=objetivos_psicolocigos, obj_tecnicos=objetivos_tecnicos, obj_tacticos=objetivos_tacticos,
            usuario=request.user.username)
        
        #y ahora los añadimos al modelo SOLO si es un ejercicio que no estaba ya
        ejerciciosEnBaseDeDatos = Ejercicio.objects.filter(nombre=ejercicio[0]).filter(descripcion=ejercicio[1]).filter(material=ejercicio[2]).filter(consejos=ejercicios[3]).filter(user=request.user)
        if len(ejerciciosEnBaseDeDatos) == 0:
            newEjercicio = Ejercicio.objects.create(nombre=ejercicio[0], descripcion=ejercicio[1], material=ejercicio[2],
                consejos=ejercicio[3], user=request.user)
            newEjercicio.objetivoEspecifico.set(objsE)
            newEjercicio.objetivoFisico.set(objsF)
            newEjercicio.objetivoPsicologico.set(objsP)
            newEjercicio.objetivoTactico.set(objsTa)
            newEjercicio.objetivoTecnico.set(objsTe)

    writer.commit()

def obtenerEjercicios(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)

    resultados = extraer_ejercicios("http://entrenamientosdefutbol.es/Buscar/")

    esquema_ejercicios(request, resultados)

    return redirect('/' + str(id_equipo) + '/ejercicios')

def confirmacion(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)

    return render(request, 'principal/confirmacion.html', {'eq':eq})

#-------------------------FIN DE LA PARTE DE WHOOSH Y BEAUTIFULSOUP DE LOS EJERCICIOS--------------------------------

def ejercicioDetails(request, id_ejercicio, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    ejercicio = get_object_or_404(Ejercicio, pk=id_ejercicio)
    tipo_consejo = ejercicio.consejos.split(" | ")
    incidir = tipo_consejo[0]
    evitar = tipo_consejo[1]
    progresion = tipo_consejo[2]
    tipo_material = ejercicio.material.split(" | ")
    material_1 = tipo_material[0]
    material_2 = tipo_material[1]
    material_3 = tipo_material[2]
    material_4 = tipo_material[3]

    return render(request, 'principal/ejercicioDetails.html', {'ejercicio': ejercicio, 'MEDIA_URL':settings.MEDIA_URL,
        'incidir':incidir, 'evitar':evitar, 'progresion':progresion, 'material_1':material_1,
        'material_2':material_2, 'material_3':material_3, 'material_4':material_4, 'eq':eq})

def buscar_ejerciciosporfiltro(request, id_equipo):
    if request.user.is_authenticated == False:
        return redirect('/login')

    eq = get_object_or_404(Equipo, pk=id_equipo)
    objetivos_fisicos = ObjetivoFisico.objects.filter(user=request.user)
    objetivos_especificos = ObjetivoEspecifico.objects.filter(user=request.user)
    objetivos_psicologicos = ObjetivoPsicologico.objects.filter(user=request.user)
    objetivos_tecnicos = ObjetivoTecnico.objects.filter(user=request.user)
    objetivos_tacticos = ObjetivoTactico.objects.filter(user=request.user)
    resultado = None
    
    if request.method=='POST':
        objetivo_fisico=request.POST['objetivos_fisicos']
        objetivo_especifico=request.POST['objetivos_especificos']
        objetivo_psicologico=request.POST['objetivos_psicologicos']
        objetivo_tecnico=request.POST['objetivos_tecnicos']
        objetivo_tactico=request.POST['objetivos_tacticos']

        ix_ejercicios = open_dir("Index_ejercicios")
        resultado = []

        with ix_ejercicios.searcher() as searcherEjercicios:
            consulta = str(objetivo_fisico) + " " + str(objetivo_especifico) + " " + str(objetivo_psicologico) + " " + str(objetivo_tecnico) + " " + str(objetivo_tactico)
            query = MultifieldParser(["obj_especificos","obj_fisicos", "obj_psicologicos",
                "obj_tacticos", "obj_tecnicos"], ix_ejercicios.schema, group=OrGroup).parse(str(consulta))
            #ponemos límite None para que nos devuelva todos los resultados
            diccionariosEjercicios = searcherEjercicios.search(query, limit=None)
            auxEjercicios = {}

            for dicEjercicios in diccionariosEjercicios:
                coincidencias = Ejercicio.objects.filter(nombre=dicEjercicios['nombre']).filter(user=request.user)
                if len(coincidencias) == 0:
                    ejercicio_id = None
                else:
                    ejercicio_id = coincidencias[0].id
                auxEjercicios = {
                    'id' : ejercicio_id,
                    'nombre' : dicEjercicios['nombre'],
                    'descripcion' : dicEjercicios['descripcion']
                }
                resultado.append(auxEjercicios)
    
    ejercicios = Ejercicio.objects.filter(user=request.user)
    
    return render(request, 'principal/ejercicios.html', { 'objetivos_fisicos': objetivos_fisicos,
        'objetivos_especificos': objetivos_especificos, 'objetivos_psicologicos': objetivos_psicologicos,
        'objetivos_tecnicos': objetivos_tecnicos, 'objetivos_tacticos': objetivos_tacticos,
        'resultado':resultado, 'ejercicios': ejercicios, 'eq':eq})
