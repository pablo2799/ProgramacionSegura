from mailbox import NoSuchMailboxError
from django.db import models
from enum import unique

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

class Maestros(models.Model): #Clase para maestros que se pueden loguear en el sistema
    maestro = models.CharField(max_length=50)
    contrasena = models.CharField(max_length=255)
    nopersonal = models.CharField(max_length=5) 
    correo = models.CharField(max_length=30)
    chatId = models.CharField(max_length=9)
    tokenId = models.CharField(max_length=46)
    token = models.CharField(max_length=4)
    vidaToken = models.DateTimeField()
    salt = models.CharField(max_length = 16, default="0")

class ejercicios(models.Model):
    descripcion = models.CharField(max_length=255)
    entrada = models.CharField(max_length=100)
    salida = models.CharField(max_length=100)