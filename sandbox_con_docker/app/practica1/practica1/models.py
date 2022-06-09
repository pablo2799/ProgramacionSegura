from ssl import _PasswordType
from django.db import models
# Create your models here.
class Maestros(models.Model): 
    nombre=models.CharField(max_length=50)
    no_personal=models.CharField(max_length=5)
    correo=models.EmailField(max_length=20)
    contrasena=models.CharField(max_length=20)

class Alumnos(models.Model): 
    nombre=models.CharField(max_length=50)
    matricula=models.CharField(max_length=9)
    correo=models.EmailField(max_length=20)
    carrera=models.CharField(max_length=30)
    contrasena=models.CharField(max_length=20)