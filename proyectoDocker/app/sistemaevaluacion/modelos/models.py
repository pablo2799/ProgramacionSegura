from mailbox import NoSuchMailboxError
from django.db import models
from enum import unique

class Peticion(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    intentos = models.IntegerField(default=1)
    timestamp = models.DateTimeField()

class Alumnos(models.Model): #Clase para usuarios que se pueden loguear en el sistema
    usuario = models.CharField(max_length=15)
    password = models.CharField(max_length=255)
    chatId = models.CharField(max_length=15)
    tokenId = models.CharField(max_length=49)
    token = models.CharField(max_length=8)
    vidaToken = models.DateTimeField()
    salt = models.CharField(max_length = 16, default="0")