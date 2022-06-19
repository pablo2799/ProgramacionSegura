from mailbox import NoSuchMailboxError
from django.db import models
from enum import unique

from pymysql import NULL

class Peticion(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    intentos = models.IntegerField(default=1)
    timestamp = models.DateTimeField()

class Alumnos(models.Model): #Clase para alumnos que se pueden loguear en el sistema
    usuario = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    matricula = models.CharField(max_length=9) 
    carrera = models.CharField(max_length=40)
    correo = models.CharField(max_length=30)
    chatId = models.CharField(max_length=9)
    tokenId = models.CharField(max_length=46)
    token = models.CharField(max_length=4)
    vidaToken = models.DateTimeField()
    salt = models.CharField(max_length = 16, default="0")
    tipouser = models.CharField(max_length=1,default="a")

class Maestros(models.Model): #Clase para maestros que se pueden loguear en el sistema
    usuario = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    nopersonal = models.CharField(max_length=5) 
    correo = models.CharField(max_length=30)
    chatId = models.CharField(max_length=9)
    tokenId = models.CharField(max_length=46)
    token = models.CharField(max_length=4)
    vidaToken = models.DateTimeField()
    salt = models.CharField(max_length = 16, default="0")
    tipouser = models.CharField(max_length=1,default="m")

class Ejerciciosmaestros(models.Model):
    titulo = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    entradaPrueba = models.CharField(max_length=100)
    salidaEsperada = models.CharField(max_length=100, null=True, blank=True)
    scriptInicial = models.FileField(upload_to='scripts-inicializacion')
    scriptComprobacionEF = models.FileField(upload_to='scripts-comprobacionEF')
    scriptComprobacionP = models.FileField(upload_to='scripts-comprobacionP')

class Ejerciciosalumnos(models.Model):
    alumno = models.ForeignKey(Alumnos,on_delete=models.SET_NULL, null=True, blank=True, max_length=50)
    ejercicio = models.ForeignKey(Ejerciciosmaestros,on_delete=models.SET_NULL, null=True, blank=True, max_length=20)
    scriptEstudiante = models.FileField(upload_to='scripts-estudiantes')
    resultadoFinal = models.CharField(max_length=10,default=NULL)
    resultadoParametros = models.CharField(max_length=10,default=NULL)