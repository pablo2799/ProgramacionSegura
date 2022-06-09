from django.contrib import admin

# Register your models here.
from .models import Peticion, Alumnos

admin.site.register(Peticion)
admin.site.register(Alumnos)