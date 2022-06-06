from django.db import models

# Create your models here.

from django.db import models

# Create your models here.

class Usuarios(models.Model):
      Nombre = models.CharField(max_length = 40)
      Matricula = models.CharField(max_length = 40)
      Contrasena = models.CharField(max_length = 100)
      Salt = models.CharField(max_length = 16, default="0")
      
