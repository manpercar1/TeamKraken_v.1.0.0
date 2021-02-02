#encoding:utf-8
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Posicion(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Posición')

    def __str__(self):
        return self.nombre
    
class ObjetivoTecnico(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Objetivo técnico')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
class ObjetivoTactico(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Objetivo táctico')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre

class ObjetivoFisico(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Objetivo físico')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre

class ObjetivoPsicologico(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Objetivo Psicológico')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre

class ObjetivoEspecifico(models.Model):
    nombre = models.CharField(max_length=30, verbose_name='Objetivo Específico')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
class Ejercicio(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    material = models.TextField(verbose_name='Material', help_text='Enumera el material necesario')
    objetivoTecnico = models.ManyToManyField(ObjetivoTecnico, blank=True)
    objetivoTactico = models.ManyToManyField(ObjetivoTactico, blank=True)
    objetivoFisico = models.ManyToManyField(ObjetivoFisico, blank=True)
    objetivoPsicologico = models.ManyToManyField(ObjetivoPsicologico, blank=True)
    objetivoEspecifico = models.ManyToManyField(ObjetivoEspecifico, blank=True)
    descripcion = models.TextField(verbose_name='Descripción', help_text='Añade una descripción')
    consejos = models.TextField(verbose_name='Consejos', help_text='Consejos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.nombre

class Equipo(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    codigo = models.CharField(max_length=50, verbose_name='Codigo')
    domicilio = models.CharField(max_length=50, verbose_name='Domicilio')
    codigoPostal = models.CharField(max_length=50, verbose_name='Codigo postal')
    localidad = models.CharField(max_length=50, verbose_name='Localidad')
    provincia = models.CharField(max_length=50, verbose_name='Provincia')
    categoria = models.CharField(max_length=50, verbose_name='Categoria')
    email = models.CharField(max_length=50, verbose_name='Email')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.nombre + ", " + self.localidad + "(" + self.provincia + ")"

class Jugador(models.Model):
    PIE_DERECHO = 'PD'
    PIE_IZQUIERDO = 'PI'
    AMBIDIESTRO = 'AM'
    PIE_DOMINANTE_CHOICES = [
        (PIE_DERECHO, 'Pie derecho'),
        (PIE_IZQUIERDO, 'Pie izquierdo'),
        (AMBIDIESTRO, 'Ambidiestro'),
    ]
    nombre = models.CharField(max_length=30, verbose_name='Nombre')
    apellidos = models.CharField(max_length=50, verbose_name='Apellidos')
    fechaNacimiento = models.CharField(max_length=50, verbose_name='Fecha de nacimiento', null=True)
    posicionPrincipal = models.CharField(max_length=30, verbose_name='Posicion principal', null=True)
    posicionesSecundarias = models.ManyToManyField(Posicion, blank=True)
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    pieDominante = models.CharField(max_length=2, choices=PIE_DOMINANTE_CHOICES, default=PIE_DERECHO)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.nombre + " " + self.apellidos

class Partido(models.Model):
    fecha = models.CharField(max_length=50, verbose_name='Fecha')
    local = models.CharField(max_length=50, verbose_name='Local')
    visitante = models.CharField(max_length=50, verbose_name='Visitante')
    resultado = models.CharField(max_length=10, verbose_name='Resultado')
    convocados = models.ManyToManyField(Jugador)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.local + " " + self.visitante

class Entrenamiento(models.Model):
    fecha = models.CharField(max_length=50, verbose_name='Fecha')
    ejercicios = models.ManyToManyField(Ejercicio)
    jugadores = models.ManyToManyField(Jugador)
    equipo = models.ForeignKey(Equipo , on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.fecha.__str__()
    
class DetallesPartido(models.Model):
    SI = 'Si'
    NO = 'No'
    TITULAR_CHOICES = [
        (SI, 'Si'),
        (NO, 'No')
        ]
    fecha = models.CharField(max_length=50, verbose_name='Fecha')
    local = models.CharField(max_length=50, verbose_name='Local')
    visitante = models.CharField(max_length=50, verbose_name='Visitante')
    resultado = models.CharField(max_length=10, verbose_name='Resultado')
    titular = models.CharField(max_length=2, choices=TITULAR_CHOICES, default=NO)
    posicion = models.ForeignKey(Posicion, on_delete=models.SET_NULL, null=True)
    tirosPuerta = models.IntegerField(verbose_name='Tiros a puerta')
    goles = models.IntegerField(verbose_name='Goles')
    asistencias = models.IntegerField(verbose_name='Asistencias')
    robosBalon = models.IntegerField(verbose_name='Robos de balon')
    balonesPerdidos = models.IntegerField(verbose_name='Balones perdidos')
    minutosJugados = models.IntegerField(verbose_name='Minutos jugados')
    amarillas = models.IntegerField(verbose_name='Amarillas')
    rojas = models.IntegerField(verbose_name='Rojas')
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, null=True)
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.local + " " + self.visitante
        
class Falta(models.Model):
    INJUSTIFICADA = 'Injustificada'
    JUSTIFICADA = 'Justificada'
    LESION = 'Lesion'
    TIPO_FALTA_CHOICES = [
        (INJUSTIFICADA, 'Injustificada'),
        (JUSTIFICADA, 'Justificada'),
        (LESION, 'Lesion'),
    ]
    fecha = models.CharField(max_length=30, verbose_name='Fecha')
    tipo = models.CharField(max_length=30, choices=TIPO_FALTA_CHOICES, default=INJUSTIFICADA)
    entrenamiento = models.ForeignKey(Entrenamiento, on_delete=models.CASCADE, null=True)
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.tipo
    

class Cooper(models.Model):
    fecha = models.CharField(max_length=30, verbose_name='Fecha')
    distancia = models.IntegerField(verbose_name='Distancia recorrida')
    vo2max = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='vo2max')
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.fecha.__str__()